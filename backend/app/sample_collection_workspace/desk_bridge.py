"""Bridge Reception (BizOrder) → SampleCollection for collector workflow.

Reception M2 creates BizOrders. Collector Queue reads SampleCollection rows.
This module ensures one active desk SampleCollection per specimen-requiring
BizOrder (idempotent) and keeps BizCollection / sample/lab queues in sync.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from app.business_engine.statuses import (
    COLLECTION_ASSIGNED as BIZ_ASSIGNED,
    COLLECTION_COLLECTED as BIZ_COLLECTED,
    COLLECTION_DELIVERED as BIZ_DELIVERED,
    COLLECTION_IN_TRANSIT as BIZ_IN_TRANSIT,
)
from app.core.statuses import (
    COLLECTION_CHECKED_IN,
    COLLECTION_COLLECTED,
    COLLECTION_IN_TRANSIT,
    COLLECTION_PENDING,
    COLLECTION_RECEIVED,
    COLLECTION_RECOLLECT_REQUIRED,
    COLLECTION_REJECTED,
)
from app.extensions.db import db
# Remove unused import if any
from app.models.biz_order import BizCollection, BizOrder
from app.models.sample_collection import SampleCollection
from app.models.sample_tracking import SampleTracking
from app.models.test_catalog import TestCatalog

logger = logging.getLogger("dxcon.desk_bridge")

DESK_SOURCE = "desk"
FIELD_SOURCE = "field"
WALK_IN_COLLECTOR = "Walk-in Collector"
RECEPTION_DESK_LOCATION = "Reception Desk"

STATUS_PENDING = "PENDING"
STATUS_ASSIGNED = "ASSIGNED"
STATUS_VERIFIED = "VERIFIED"
STATUS_COLLECTED = "COLLECTED"
STATUS_IN_TRANSIT = "IN_TRANSIT"
STATUS_ARRIVED_AT_LAB = "ARRIVED_AT_LAB"

# Statuses that mean the specimen has arrived at the laboratory (sync + queue)
LAB_ARRIVAL_DB_STATUSES = frozenset(
    {
        COLLECTION_RECEIVED,
        STATUS_ARRIVED_AT_LAB,
        "ARRIVED_AT_LAB",
        "RECEIVED",
        "delivered",
    }
)

# Sample types that do not require physical specimen collection
NON_SPECIMEN_SAMPLE_TYPES = frozenset(
    {
        "",
        "none",
        "n/a",
        "na",
        "consult",
        "consultation",
        "interpretation",
        "report",
        "report_only",
        "document",
        "service",
    }
)

BIZ_TO_CANONICAL = {
    "assigned": STATUS_PENDING,
    "accepted": STATUS_VERIFIED,
    "collected": STATUS_COLLECTED,
    "in_transit": STATUS_IN_TRANSIT,
    "delivered": STATUS_ARRIVED_AT_LAB,
    "cancelled": COLLECTION_REJECTED,
}

CLINICAL_TO_CANONICAL = {
    COLLECTION_PENDING: STATUS_PENDING,
    COLLECTION_CHECKED_IN: STATUS_VERIFIED,
    COLLECTION_COLLECTED: STATUS_COLLECTED,
    COLLECTION_IN_TRANSIT: STATUS_IN_TRANSIT,
    COLLECTION_RECEIVED: STATUS_ARRIVED_AT_LAB,
    COLLECTION_REJECTED: COLLECTION_REJECTED,
    STATUS_ASSIGNED: STATUS_PENDING,
    STATUS_VERIFIED: STATUS_VERIFIED,
    STATUS_ARRIVED_AT_LAB: STATUS_ARRIVED_AT_LAB,
    "AWAITING_COLLECTION": STATUS_PENDING,
}

# API filter aliases → DB SampleCollection statuses
FILTER_STATUS_TO_DB = {
    STATUS_PENDING: (COLLECTION_PENDING, STATUS_ASSIGNED, "assigned", "AWAITING_COLLECTION"),
    STATUS_ASSIGNED: (COLLECTION_PENDING, STATUS_ASSIGNED, "assigned"),
    "AWAITING_COLLECTION": (COLLECTION_PENDING, STATUS_ASSIGNED, "assigned", "AWAITING_COLLECTION"),
    STATUS_VERIFIED: (COLLECTION_PENDING, COLLECTION_CHECKED_IN, STATUS_ASSIGNED),
    "CHECKED_IN": (COLLECTION_CHECKED_IN, COLLECTION_PENDING),
    STATUS_COLLECTED: (COLLECTION_COLLECTED,),
    STATUS_IN_TRANSIT: (COLLECTION_IN_TRANSIT,),
    STATUS_ARRIVED_AT_LAB: (COLLECTION_RECEIVED,),
    "RECEIVED": (COLLECTION_RECEIVED,),
    COLLECTION_REJECTED: (COLLECTION_REJECTED,),
}

# Default Collector Queue "Awaiting" eligibility (stored DB values)
AWAITING_QUEUE_DB_STATUSES = (
    COLLECTION_PENDING,
    STATUS_ASSIGNED,
    "assigned",
    "AWAITING_COLLECTION",
    COLLECTION_CHECKED_IN,
    COLLECTION_RECOLLECT_REQUIRED,
)


def order_requires_specimen_collection(order: BizOrder) -> bool:
    """True when at least one order line needs a physical specimen."""
    items = list(order.items or [])
    if not items:
        # Empty order should not enqueue; create_reception_order requires tests.
        return False
    for item in items:
        sample_type = None
        if item.test_catalog_id:
            catalog = TestCatalog.query.get(item.test_catalog_id)
            if catalog and catalog.sample_type is not None:
                sample_type = catalog.sample_type
        if sample_type is None:
            sample_type = getattr(item, "sample_type", None)
        normalized = str(sample_type or "").strip().lower()
        if normalized in NON_SPECIMEN_SAMPLE_TYPES:
            continue
        # Unknown / Blood / Serum / etc. → requires collection
        return True
    return False


def normalize_collection_status(
    status: str | None,
    *,
    patient_verified: bool = False,
    order_verified: bool = False,
) -> str:
    raw = (status or "").strip()
    if not raw:
        return STATUS_PENDING
    upper = raw.upper()
    lower = raw.lower()
    if lower in BIZ_TO_CANONICAL:
        canonical = BIZ_TO_CANONICAL[lower]
    elif upper in CLINICAL_TO_CANONICAL:
        canonical = CLINICAL_TO_CANONICAL[upper]
    else:
        canonical = upper
    if canonical == STATUS_PENDING and patient_verified and order_verified:
        return STATUS_VERIFIED
    return canonical


def is_terminal_status(status: str | None) -> bool:
    canonical = normalize_collection_status(status)
    return canonical in {
        STATUS_ARRIVED_AT_LAB,
        COLLECTION_REJECTED,
        "CANCELLED",
        "COMPLETED",
        "RECEIVED",
    }


def resolve_filter_statuses(status: str | None) -> list[str] | None:
    if not status:
        return None
    parts = [s.strip() for s in str(status).split(",") if s.strip()]
    resolved: list[str] = []
    for part in parts:
        key = part.upper()
        mapped = FILTER_STATUS_TO_DB.get(key)
        if mapped:
            resolved.extend(mapped)
        else:
            resolved.append(part)
    seen: set[str] = set()
    out: list[str] = []
    for value in resolved:
        if value not in seen:
            seen.add(value)
            out.append(value)
    return out


def collection_source(collection: SampleCollection | dict[str, Any]) -> str:
    if isinstance(collection, dict):
        explicit = collection.get("source")
        if explicit in {DESK_SOURCE, FIELD_SOURCE}:
            return explicit
        if collection.get("marketplace_booking_id"):
            return FIELD_SOURCE
        notes = str(collection.get("notes") or "")
        if "source:desk" in notes:
            return DESK_SOURCE
        return DESK_SOURCE
    if collection.marketplace_booking_id:
        return FIELD_SOURCE
    return DESK_SOURCE


def _sample_collection_columns() -> set[str]:
    try:
        from app.services.sample_collection_workflow import SampleCollectionWorkflowService

        return set(SampleCollectionWorkflowService._sample_collection_db_columns() or set())
    except Exception:
        return set()


def _apply_if_column(kwargs: dict[str, Any], columns: set[str], name: str, value: Any) -> None:
    if not columns or name in columns:
        kwargs[name] = value


def ensure_desk_sample_collection(
    order: BizOrder,
    *,
    actor: str | None = None,
    organization_id: str | None = None,
    commit: bool = False,
    require_specimen: bool | None = None,
) -> SampleCollection | None:
    """Deprecated alias → ensure_collection_for_order(..., AT_RECEPTION)."""
    from app.sample_collection_workspace.collection_domain import MODE_AT_RECEPTION
    from app.sample_collection_workspace.collection_routing import ensure_collection_for_order

    if require_specimen is False:
        return None
    if require_specimen is None and not order_requires_specimen_collection(order):
        return None
    return ensure_collection_for_order(
        order,
        collection_mode=MODE_AT_RECEPTION,
        organization_id=organization_id,
        actor=actor,
        commit=commit,
    )

def ensure_biz_collection_row(
    order: BizOrder,
    *,
    actor: str | None = None,
    status: str = BIZ_ASSIGNED,
) -> BizCollection:
    """Create BizCollection without requiring paid order (desk bridge)."""
    existing = BizCollection.query.filter_by(order_id=order.id).first()
    if existing:
        return existing
    sample_code = f"SMP-{order.order_code}"
    row = BizCollection(
        order_id=order.id,
        collector_name=actor or WALK_IN_COLLECTOR,
        pickup_address=RECEPTION_DESK_LOCATION,
        scheduled_at=datetime.utcnow(),
        status=status,
        sample_code=sample_code,
        barcode_value=order.barcode_value or f"BC-{sample_code}",
    )
    db.session.add(row)
    db.session.flush()
    return row


def sync_biz_collection_from_sample(
    collection: SampleCollection,
    *,
    actor: str | None = None,
) -> BizCollection | None:
    """Mirror SampleCollection clinical status onto BizCollection for sample/lab queues."""
    order = BizOrder.query.get(collection.order_id)
    if not order:
        return None
    biz_row = ensure_biz_collection_row(order, actor=actor or WALK_IN_COLLECTOR)

    status = collection.status
    if status in {COLLECTION_PENDING, COLLECTION_CHECKED_IN, STATUS_ASSIGNED, "assigned"}:
        if biz_row.status not in {BIZ_ASSIGNED, "accepted", BIZ_COLLECTED, BIZ_IN_TRANSIT, BIZ_DELIVERED}:
            biz_row.status = BIZ_ASSIGNED
        if (order.status or "").lower() in {"draft", "payment_pending", "paid"}:
            order.status = "sampling"
    elif status == COLLECTION_COLLECTED:
        biz_row.status = BIZ_COLLECTED
        order.status = "collected"
    elif status == COLLECTION_IN_TRANSIT:
        biz_row.status = BIZ_IN_TRANSIT
        order.status = "in_transit"
    elif status in LAB_ARRIVAL_DB_STATUSES:
        biz_row.status = BIZ_DELIVERED
        order.status = "lab_received"
        if not collection.arrived_at_lab:
            collection.arrived_at_lab = datetime.utcnow()
    biz_row.updated_at = datetime.utcnow()
    order.updated_at = datetime.utcnow()
    if collection.barcode_value:
        biz_row.barcode_value = collection.barcode_value
    if collection.collector_name:
        biz_row.collector_name = collection.collector_name
    db.session.flush()
    return biz_row


def enqueue_sample_and_lab_after_transition(
    collection: SampleCollection,
    *,
    actor: str | None = None,
) -> dict[str, Any]:
    """After COLLECTED/IN_TRANSIT/lab-arrival, sync reception sample queue + lab queue."""
    result: dict[str, Any] = {}
    arrived = collection.status in LAB_ARRIVAL_DB_STATUSES
    if collection.marketplace_booking_id and not arrived:
        return result

    order = BizOrder.query.get(collection.order_id)
    if not order:
        return result

    sync_biz_collection_from_sample(collection, actor=actor)

    if collection.status in {COLLECTION_COLLECTED, COLLECTION_IN_TRANSIT} or arrived:
        try:
            from app.reception_workspace.sample_queue_engine import (
                STAGE_COLLECTED,
                STAGE_RECEIVED,
                STAGE_TRANSPORT,
                advance_sample_queue,
                ensure_sample_queue_item,
                get_sample_queue_item,
            )

            ensure_sample_queue_item(order.order_code, actor=actor, sync_collection=False)
            item = get_sample_queue_item(order.order_code)
            if item:
                if collection.status == COLLECTION_IN_TRANSIT and item.stage == STAGE_COLLECTED:
                    advance_sample_queue(
                        order.order_code,
                        to_stage=STAGE_TRANSPORT,
                        actor=actor,
                        sync_collection=False,
                    )
                elif arrived and item.stage in {
                    STAGE_COLLECTED,
                    STAGE_TRANSPORT,
                }:
                    if item.stage == STAGE_COLLECTED:
                        advance_sample_queue(
                            order.order_code,
                            to_stage=STAGE_TRANSPORT,
                            actor=actor,
                            sync_collection=False,
                        )
                    item = get_sample_queue_item(order.order_code)
                    if item and item.stage == STAGE_TRANSPORT:
                        advance_sample_queue(
                            order.order_code,
                            to_stage=STAGE_RECEIVED,
                            actor=actor,
                            sync_collection=False,
                        )
            result["sample_queue"] = True
        except Exception as exc:
            result["sample_queue_error"] = str(exc)

    if arrived:
        try:
            from app.reception_workspace.lab_queue_engine import ensure_lab_queue_item

            ensure_lab_queue_item(order.order_code, actor=actor)
            result["lab_queue"] = True
            result["order_status"] = order.status
        except Exception as exc:
            result["lab_queue_error"] = str(exc)

    return result


def annotate_queue_item(item: dict[str, Any]) -> dict[str, Any]:
    """Normalize status + source + actionable flag for collector UI."""
    source = collection_source(item)
    item["source"] = source
    raw_status = item.get("status")
    item["status_raw"] = raw_status
    status = normalize_collection_status(
        raw_status,
        patient_verified=bool(item.get("patient_verified")),
        order_verified=bool(item.get("order_verified")),
    )
    item["status"] = status
    item["actionable"] = not is_terminal_status(status)

    if source == DESK_SOURCE:
        if not item.get("collector_name"):
            item["collector_name"] = WALK_IN_COLLECTOR
        if not item.get("collection_location") and not item.get("pickup_address"):
            item["collection_location"] = RECEPTION_DESK_LOCATION
        if not item.get("booking"):
            order = item.get("order") or {}
            item["booking"] = {
                "patient_name": order.get("patient_name"),
                "booking_code": order.get("order_code"),
                "patient_address": item.get("collection_location")
                or item.get("pickup_address")
                or RECEPTION_DESK_LOCATION,
                "city": item.get("location_city"),
            }
    return item


def backfill_desk_sample_collections(*, limit: int = 200) -> int:
    """Ensure SampleCollection exists for active BizCollection desk jobs."""
    created = 0
    rows = (
        BizCollection.query.filter(
            BizCollection.status.in_((BIZ_ASSIGNED, "accepted", BIZ_COLLECTED, BIZ_IN_TRANSIT))
        )
        .order_by(BizCollection.created_at.desc())
        .limit(limit)
        .all()
    )
    for row in rows:
        order = BizOrder.query.get(row.order_id)
        if not order:
            continue
        before = SampleCollection.query.filter_by(order_id=order.id).count()
        ensure_desk_sample_collection(order, require_specimen=True)
        after = SampleCollection.query.filter_by(order_id=order.id).count()
        if after > before:
            created += 1
            sc = (
                SampleCollection.query.filter_by(order_id=order.id)
                .order_by(SampleCollection.created_at.desc())
                .first()
            )
            if sc and sc.status == COLLECTION_PENDING:
                if row.status == BIZ_COLLECTED:
                    sc.status = COLLECTION_COLLECTED
                elif row.status == BIZ_IN_TRANSIT:
                    sc.status = COLLECTION_IN_TRANSIT
                elif row.status == "accepted":
                    sc.patient_verified = True
                    sc.order_verified = True
    if created:
        db.session.flush()
    return created


def ensure_desk_tracking(collection: SampleCollection, *, sample_code: str | None = None) -> SampleTracking:
    if collection.sample_tracking_id:
        existing = SampleTracking.query.get(collection.sample_tracking_id)
        if existing:
            return existing
    order = BizOrder.query.get(collection.order_id)
    code = sample_code or (f"SMP-{order.order_code}" if order else f"SMP-{collection.id[:8].upper()}")
    tracking = SampleTracking.query.filter_by(sample_code=code).first()
    if not tracking:
        tracking = SampleTracking(
            sample_code=code,
            marketplace_booking_id=None,
            collector_id=collection.collector_id,
            status="COLLECTED",
        )
        db.session.add(tracking)
        db.session.flush()
    collection.sample_tracking_id = tracking.id
    db.session.flush()
    return tracking
