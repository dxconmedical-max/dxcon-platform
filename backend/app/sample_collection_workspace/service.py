"""Sample Collection production workspace facade."""

from __future__ import annotations

from typing import Any

from app.business_engine import service as biz
from app.business_engine.statuses import (
    COLLECTION_ACCEPTED as BIZ_ACCEPTED,
    COLLECTION_ASSIGNED as BIZ_ASSIGNED,
)
from app.core.statuses import COLLECTION_QUEUE_STATUSES
from app.extensions.db import db
from app.models.biz_order import BizCollection
from app.sample_collection_workspace.desk_bridge import (
    annotate_queue_item,
    backfill_desk_sample_collections,
    collection_source,
)
from app.services.sample_collection_workflow import (
    SampleCollectionWorkflowError,
    SampleCollectionWorkflowService,
)


def workspace_dashboard() -> dict[str, Any]:
    awaiting = SampleCollectionWorkflowService.list_queue(awaiting_only=True)
    in_transit = SampleCollectionWorkflowService.list_queue(
        status="IN_TRANSIT",
        awaiting_only=False,
    )
    received = SampleCollectionWorkflowService.list_queue(
        status="RECEIVED",
        awaiting_only=False,
    )
    rejected = SampleCollectionWorkflowService.list_queue(
        status="REJECTED",
        awaiting_only=False,
    )
    biz_awaiting = (
        BizCollection.query.filter(BizCollection.status.in_((BIZ_ASSIGNED, BIZ_ACCEPTED)))
        .count()
    )
    return {
        "kpis": {
            "awaiting_collection": len(awaiting),
            "in_transit": len(in_transit),
            "arrived_at_lab": len(received),
            "rejected": len(rejected),
            "desk_jobs_awaiting": biz_awaiting,
        },
        "status_contract": {
            "queue": list(COLLECTION_QUEUE_STATUSES),
            "flow": [
                "PENDING",
                "ASSIGNED",
                "VERIFIED",
                "COLLECTED",
                "IN_TRANSIT",
                "ARRIVED_AT_LAB",
            ],
            "aliases": {
                "ASSIGNED": "PENDING",
                "CHECKED_IN": "VERIFIED",
                "RECEIVED": "ARRIVED_AT_LAB",
            },
            "exceptions": ["REJECTED", "RECOLLECT_REQUIRED"],
        },
    }


def list_production_queue(
    *,
    status: str | None = None,
    collector_id: str | None = None,
    location: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    partner_id: str | None = None,
    include_desk: bool = True,
    role: str | None = None,
    scoped_collector_id: str | None = None,
    organization_id: str | None = None,
) -> dict[str, Any]:
    """Tenant/role isolation: collectors only see their jobs; supervisors see all.

    Desk SampleCollections (null marketplace_booking_id) are first-class queue rows.
    They are never excluded by include_desk — that flag only controls legacy BizCollection
    backfill. Organization scope uses partner_id when provided (desk rows stamped at create).
    """
    effective_collector = collector_id
    if role in {"COLLECTOR", "PARTNER_COLLECTOR", "DRIVER"} and scoped_collector_id:
        effective_collector = scoped_collector_id

    # Partner filter: explicit partner_id wins. Organization header scopes only
    # collector-class roles so SUPER_ADMIN can still see the full queue.
    effective_partner = partner_id
    if not effective_partner and organization_id and role in {
        "COLLECTOR",
        "PARTNER_COLLECTOR",
        "DRIVER",
    }:
        effective_partner = organization_id

    # Always attempt backfill for desk jobs so Reception → Collector routing stays intact
    # even when clients omit include_desk.
    if not effective_collector:
        try:
            backfill_desk_sample_collections()
            db.session.commit()
        except Exception:
            db.session.rollback()

    field_items = SampleCollectionWorkflowService.list_queue(
        status=status,
        collector_id=effective_collector,
        location=location,
        date_from=date_from,
        date_to=date_to,
        partner_id=effective_partner,
        awaiting_only=not bool(status),
    )

    items: list[dict[str, Any]] = []
    for item in field_items:
        source = collection_source(item)
        item["source"] = source
        # Desk SampleCollections are always included. include_desk only gates
        # whether we ran legacy BizCollection backfill above — never silently
        # drops authoritative desk SampleCollection rows.
        items.append(annotate_queue_item(item))

    desk_count = sum(1 for item in items if item.get("source") == "desk")
    field_count = len(items) - desk_count

    return {
        "count": len(items),
        "items": items,
        "field_count": field_count,
        "desk_count": desk_count,
        "include_desk": include_desk,
    }


def collect_from_queue(
    collection_id: str,
    payload: dict[str, Any],
    *,
    actor: str | None = None,
    ip_address: str = "",
) -> dict[str, Any]:
    collection, sample = SampleCollectionWorkflowService.record_collection_by_id(
        collection_id,
        collector_id=payload.get("collector_id"),
        note=payload.get("notes") or payload.get("note"),
        latitude=payload.get("latitude"),
        longitude=payload.get("longitude"),
        actor_email=actor or "SYSTEM",
        ip_address=ip_address,
        specimen_type=payload.get("specimen_type"),
        scanned_barcode=payload.get("scanned_barcode") or payload.get("barcode"),
        collection_location=payload.get("collection_location") or payload.get("location"),
        require_barcode=bool(payload.get("require_barcode", True)),
        patient_verified=payload.get("patient_verified", True),
        order_verified=payload.get("order_verified", True),
        allow_notes=True,
    )
    return {
        "collection": SampleCollectionWorkflowService._enrich_payload(collection),
        "sample_tracking": sample.to_dict(),
    }


def desk_collect_and_transit(order_ref: str, *, actor: str | None = None) -> dict[str, Any]:
    """Advance a desk BizCollection through collect → transit (not lab receive)."""
    collection = biz.collect_sample(order_ref, actor=actor)
    collection = biz.handover_sample(order_ref, actor=actor)
    db.session.commit()
    return {"collection": collection.to_dict()}
