"""Bridge Reception (BizOrder) → SampleCollection for collector workflow.

Reception M2 creates BizOrders. Collector workflow operates on SampleCollection.
This module ensures one active desk SampleCollection per BizOrder (idempotent)
and keeps BizCollection / sample-queue / lab-queue in sync on transitions.
"""

from __future__ import annotations

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
    COLLECTION_REJECTED,
)
from app.extensions.db import db
from app.models.biz_order import BizCollection, BizOrder
from app.models.sample_collection import SampleCollection
from app.models.sample_tracking import SampleTracking

DESK_SOURCE = "desk"
FIELD_SOURCE = "field"

STATUS_PENDING = "PENDING"
STATUS_ASSIGNED = "ASSIGNED"
STATUS_VERIFIED = "VERIFIED"
STATUS_COLLECTED = "COLLECTED"
STATUS_IN_TRANSIT = "IN_TRANSIT"
STATUS_ARRIVED_AT_LAB = "ARRIVED_AT_LAB"

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
}

# API filter aliases → DB SampleCollection statuses
FILTER_STATUS_TO_DB = {
    STATUS_PENDING: (COLLECTION_PENDING,),
    STATUS_ASSIGNED: (COLLECTION_PENDING,),
    STATUS_VERIFIED: (COLLECTION_PENDING, COLLECTION_CHECKED_IN),
    "CHECKED_IN": (COLLECTION_CHECKED_IN, COLLECTION_PENDING),
    STATUS_COLLECTED: (COLLECTION_COLLECTED,),
    STATUS_IN_TRANSIT: (COLLECTION_IN_TRANSIT,),
    STATUS_ARRIVED_AT_LAB: (COLLECTION_RECEIVED,),
    "RECEIVED": (COLLECTION_RECEIVED,),
    COLLECTION_REJECTED: (COLLECTION_REJECTED,),
}


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
    # unique preserve order
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


def ensure_desk_sample_collection(
    order: BizOrder,
    *,
    actor: str | None = None,
    commit: bool = False,
) -> SampleCollection:
    """Idempotent: one active SampleCollection per BizOrder requiring specimen."""
    del actor  # reserved for audit callers
    existing = (
        SampleCollection.query.filter_by(order_id=order.id)
        .filter(SampleCollection.status != COLLECTION_REJECTED)
        .order_by(SampleCollection.created_at.desc())
        .first()
    )
    if existing:
        notes = existing.notes or ""
        if "source:desk" not in notes:
            existing.notes = (notes + "\nsource:desk").strip()
        if not existing.expected_barcode:
            existing.expected_barcode = order.barcode_value or f"BC-{order.order_code}"
        if commit:
            db.session.commit()
        else:
            db.session.flush()
        return existing

    if not order.barcode_value:
        order.barcode_value = f"BC-{order.order_code}"

    collection = SampleCollection(
        order_id=order.id,
        marketplace_booking_id=None,
        status=COLLECTION_PENDING,
        collector_name=None,
        collection_location="Reception Desk",
        location_city=None,
        expected_barcode=order.barcode_value,
        barcode_value=None,
        notes="source:desk",
        patient_verified=False,
        order_verified=False,
        specimen_type="BLOOD",
    )
    db.session.add(collection)
    db.session.flush()

    if commit:
        db.session.commit()
    return collection


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
        collector_name=actor or "Reception Desk",
        pickup_address="Reception Desk",
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
    biz_row = ensure_biz_collection_row(order, actor=actor)

    status = collection.status
    if status in {COLLECTION_PENDING, COLLECTION_CHECKED_IN}:
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
    elif status == COLLECTION_RECEIVED:
        biz_row.status = BIZ_DELIVERED
        order.status = "lab_received"
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
    """After COLLECTED/IN_TRANSIT/RECEIVED, sync reception sample queue + lab queue."""
    result: dict[str, Any] = {}
    if collection.marketplace_booking_id:
        # Field marketplace path — reception sample queue is desk-oriented
        if collection.status != COLLECTION_RECEIVED:
            return result
        # Still allow lab queue bridge when desk order id happens to be set
        order = BizOrder.query.get(collection.order_id)
        if not order:
            return result

    order = BizOrder.query.get(collection.order_id)
    if not order:
        return result

    sync_biz_collection_from_sample(collection, actor=actor)

    if collection.status in {COLLECTION_COLLECTED, COLLECTION_IN_TRANSIT, COLLECTION_RECEIVED}:
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
                elif collection.status == COLLECTION_RECEIVED and item.stage in {
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

    if collection.status == COLLECTION_RECEIVED:
        try:
            from app.reception_workspace.lab_queue_engine import ensure_lab_queue_item

            ensure_lab_queue_item(order.order_code, actor=actor)
            result["lab_queue"] = True
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

    if source == DESK_SOURCE and not item.get("booking"):
        order = item.get("order") or {}
        item["booking"] = {
            "patient_name": order.get("patient_name"),
            "booking_code": order.get("order_code"),
            "patient_address": item.get("collection_location")
            or item.get("pickup_address")
            or "Reception Desk",
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
        ensure_desk_sample_collection(order)
        after = SampleCollection.query.filter_by(order_id=order.id).count()
        if after > before:
            created += 1
            # Mirror biz status onto new SC when already progressed
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
