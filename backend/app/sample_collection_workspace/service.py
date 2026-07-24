"""Sample Collection production workspace facade."""

from __future__ import annotations

from typing import Any

from app.business_engine import service as biz
from app.business_engine.statuses import (
    COLLECTION_ACCEPTED as BIZ_ACCEPTED,
    COLLECTION_ASSIGNED as BIZ_ASSIGNED,
    COLLECTION_COLLECTED as BIZ_COLLECTED,
    COLLECTION_IN_TRANSIT as BIZ_IN_TRANSIT,
    COLLECTION_DELIVERED as BIZ_DELIVERED,
)
from app.core.statuses import COLLECTION_QUEUE_STATUSES
from app.extensions.db import db
from app.models.biz_order import BizCollection, BizOrder
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
                "CHECKED_IN",
                "COLLECTED",
                "IN_TRANSIT",
                "RECEIVED",
            ],
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
) -> dict[str, Any]:
    """Tenant/role isolation: collectors only see their jobs; supervisors see all."""
    effective_collector = collector_id
    if role in {"COLLECTOR", "PARTNER_COLLECTOR", "DRIVER"} and scoped_collector_id:
        effective_collector = scoped_collector_id

    field_items = SampleCollectionWorkflowService.list_queue(
        status=status,
        collector_id=effective_collector,
        location=location,
        date_from=date_from,
        date_to=date_to,
        partner_id=partner_id,
        awaiting_only=not bool(status),
    )

    desk_items: list[dict[str, Any]] = []
    if include_desk and not effective_collector:
        query = BizCollection.query
        if status:
            # Map clinical uppercase to biz lowercase when filtering desk jobs
            mapped = {
                "PENDING": BIZ_ASSIGNED,
                "CHECKED_IN": BIZ_ACCEPTED,
                "COLLECTED": BIZ_COLLECTED,
                "IN_TRANSIT": BIZ_IN_TRANSIT,
                "RECEIVED": BIZ_DELIVERED,
            }.get(status.upper(), status.lower())
            query = query.filter(BizCollection.status == mapped)
        else:
            query = query.filter(BizCollection.status.in_((BIZ_ASSIGNED, BIZ_ACCEPTED)))
        if location:
            like = f"%{location}%"
            query = query.filter(BizCollection.pickup_address.ilike(like))
        for row in query.order_by(BizCollection.created_at.desc()).limit(200).all():
            order = BizOrder.query.get(row.order_id)
            desk_items.append(
                {
                    "source": "desk",
                    "id": row.id,
                    "status": row.status,
                    "sample_code": row.sample_code,
                    "barcode_value": row.barcode_value,
                    "collector_name": row.collector_name,
                    "pickup_address": row.pickup_address,
                    "scheduled_at": row.scheduled_at.isoformat() if row.scheduled_at else None,
                    "order": order.to_dict() if order else None,
                    "collection": row.to_dict(),
                }
            )

    for item in field_items:
        item["source"] = "field"

    return {
        "count": len(field_items) + len(desk_items),
        "items": field_items + desk_items,
        "field_count": len(field_items),
        "desk_count": len(desk_items),
    }


def collect_from_queue(
    collection_id: str,
    payload: dict[str, Any],
    *,
    actor: str | None = None,
    ip_address: str = "",
) -> dict[str, Any]:
    detail = SampleCollectionWorkflowService.get_collection(collection_id)
    booking_id = detail.get("marketplace_booking_id")
    if not booking_id:
        raise SampleCollectionWorkflowError("Collection has no booking to collect", 409)

    collection, sample = SampleCollectionWorkflowService.record_collection(
        booking_id,
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
