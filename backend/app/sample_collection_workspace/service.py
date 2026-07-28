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
from app.sample_collection_workspace.collection_domain import (
    CANONICAL_STATUSES,
    MODE_AT_RECEPTION,
    MODE_CLINIC_COLLECTION,
    MODE_HOME_COLLECTION,
)
from app.services.sample_collection_workflow import (
    SampleCollectionWorkflowError,
    SampleCollectionWorkflowService,
)


def workspace_dashboard() -> dict[str, Any]:
    from app.sample_collection_workspace.collection_routing import (
        list_field_collector_queue,
        list_reception_desk_queue,
    )

    field = list_field_collector_queue()
    desk = list_reception_desk_queue()
    in_transit = SampleCollectionWorkflowService.list_queue(
        status="IN_TRANSIT",
        awaiting_only=False,
    )
    arrived = SampleCollectionWorkflowService.list_queue(
        status="ARRIVED_AT_LAB",
        awaiting_only=False,
    )
    if not arrived:
        arrived = SampleCollectionWorkflowService.list_queue(
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
            "awaiting_collection": field["count"],
            "desk_collections_awaiting": desk["count"],
            "in_transit": len(in_transit),
            "arrived_at_lab": len(arrived),
            "rejected": len(rejected),
            "desk_jobs_awaiting": biz_awaiting,
        },
        "status_contract": {
            "canonical": list(CANONICAL_STATUSES),
            "flow": [
                "REQUESTED",
                "ASSIGNED",
                "VERIFIED",
                "COLLECTED",
                "IN_TRANSIT",
                "ARRIVED_AT_LAB",
                "RECEIVED",
            ],
            "modes": [MODE_AT_RECEPTION, MODE_HOME_COLLECTION, MODE_CLINIC_COLLECTION],
            "queues": {
                "reception_desk": [MODE_AT_RECEPTION],
                "field_collector": [MODE_HOME_COLLECTION, MODE_CLINIC_COLLECTION],
            },
            "legacy_queue": list(COLLECTION_QUEUE_STATUSES),
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
    include_desk: bool = False,
    role: str | None = None,
    scoped_collector_id: str | None = None,
    organization_id: str | None = None,
    queue: str | None = None,
) -> dict[str, Any]:
    """Collector field queue by default (HOME/CLINIC only).

    include_desk is deprecated for merging desks into the field queue.
    Use queue=desk or GET /reception/.../desk-collections for AT_RECEPTION.
    """
    from app.sample_collection_workspace.collection_routing import (
        list_field_collector_queue,
        list_reception_desk_queue,
    )

    effective_collector = collector_id
    if role in {"COLLECTOR", "PARTNER_COLLECTOR", "DRIVER"} and scoped_collector_id:
        effective_collector = scoped_collector_id

    effective_partner = partner_id
    if not effective_partner and organization_id and role in {
        "COLLECTOR",
        "PARTNER_COLLECTOR",
        "DRIVER",
    }:
        effective_partner = organization_id

    queue_kind = (queue or "").strip().lower()
    if queue_kind in {"desk", "reception", "at_reception"} or include_desk is True and queue_kind == "all":
        if queue_kind in {"desk", "reception", "at_reception"}:
            return list_reception_desk_queue(
                status=status,
                location=location,
                date_from=date_from,
                date_to=date_to,
                partner_id=effective_partner,
                role=role,
                organization_id=organization_id,
            )

    if queue_kind == "all":
        # Explicit all — still annotate by mode; used by admin diagnostics only
        field = list_field_collector_queue(
            status=status,
            collector_id=effective_collector,
            location=location,
            date_from=date_from,
            date_to=date_to,
            partner_id=effective_partner,
            role=role,
            organization_id=organization_id,
        )
        desk = list_reception_desk_queue(
            status=status,
            location=location,
            date_from=date_from,
            date_to=date_to,
            partner_id=effective_partner,
            role=role,
            organization_id=organization_id,
        )
        items = field["items"] + desk["items"]
        return {
            "count": len(items),
            "items": items,
            "field_count": field["count"],
            "desk_count": desk["count"],
            "queue": "all",
        }

    # Default: field collector queue only (never merge AT_RECEPTION)
    payload = list_field_collector_queue(
        status=status,
        collector_id=effective_collector,
        location=location,
        date_from=date_from,
        date_to=date_to,
        partner_id=effective_partner,
        role=role,
        organization_id=organization_id,
    )
    payload["field_count"] = payload["count"]
    payload["desk_count"] = 0
    return payload


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
