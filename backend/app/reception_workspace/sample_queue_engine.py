"""Sample Queue — logistics tracking after specimen draw.

Workflow: collected → transport → received → sorting → laboratory → completed
"""

from __future__ import annotations

import hashlib
from datetime import datetime
from typing import Any

from sqlalchemy import or_

from app.business_engine import service as biz
from app.business_engine.service import BusinessEngineError
from app.business_engine.statuses import (
    COLLECTION_COLLECTED,
    COLLECTION_DELIVERED,
    COLLECTION_IN_TRANSIT,
    ORDER_LAB_RECEIVED,
)
from app.extensions.db import db
from app.models.biz_order import (
    BizCollection,
    BizOrder,
    BizSampleQueueEvent,
    BizSampleQueueItem,
)
from app.reception_workspace.audit import write_reception_audit
from app.reception_workspace.errors import ReceptionWorkspaceError

STAGE_COLLECTED = "collected"
STAGE_TRANSPORT = "transport"
STAGE_RECEIVED = "received"
STAGE_SORTING = "sorting"
STAGE_LABORATORY = "laboratory"
STAGE_COMPLETED = "completed"

QUEUE_STAGES = (
    STAGE_COLLECTED,
    STAGE_TRANSPORT,
    STAGE_RECEIVED,
    STAGE_SORTING,
    STAGE_LABORATORY,
    STAGE_COMPLETED,
)

STAGE_TRANSITIONS: dict[str, tuple[str, ...]] = {
    STAGE_COLLECTED: (STAGE_TRANSPORT,),
    STAGE_TRANSPORT: (STAGE_RECEIVED,),
    STAGE_RECEIVED: (STAGE_SORTING,),
    STAGE_SORTING: (STAGE_LABORATORY,),
    STAGE_LABORATORY: (STAGE_COMPLETED,),
    STAGE_COMPLETED: (),
}

PIPELINE = list(QUEUE_STAGES)


def _utcnow() -> datetime:
    return datetime.utcnow()


def normalize_stage(stage: str | None) -> str:
    raw = (stage or "").strip().lower()
    if raw not in QUEUE_STAGES:
        raise ReceptionWorkspaceError(f"Invalid sample queue stage: {stage}")
    return raw


def _resolve_order(order_ref: str) -> BizOrder:
    order = BizOrder.query.filter(
        or_(BizOrder.order_code == order_ref, BizOrder.id == order_ref)
    ).first()
    if not order:
        raise ReceptionWorkspaceError("Order not found")
    return order


def get_sample_queue_item(order_ref: str) -> BizSampleQueueItem | None:
    return BizSampleQueueItem.query.filter(
        or_(
            BizSampleQueueItem.order_code == order_ref,
            BizSampleQueueItem.order_id == order_ref,
        )
    ).first()


def _append_event(
    item: BizSampleQueueItem,
    *,
    event_type: str,
    from_stage: str | None,
    to_stage: str | None,
    actor: str | None,
    note: str | None = None,
    location: str | None = None,
) -> BizSampleQueueEvent:
    event = BizSampleQueueEvent(
        queue_item_id=item.id,
        order_code=item.order_code,
        event_type=event_type,
        from_stage=from_stage,
        to_stage=to_stage,
        actor=actor or "SYSTEM",
        location=location or item.location,
        note=note,
        created_at=_utcnow(),
    )
    db.session.add(event)
    db.session.flush()
    write_reception_audit(
        action=f"sample_queue_{event_type}",
        object_type="sample_queue",
        object_id=item.order_code,
        actor=actor,
    )
    return event


def _serialize_item(
    item: BizSampleQueueItem,
    order: BizOrder | None = None,
    *,
    include_history: bool = False,
) -> dict[str, Any]:
    order = order or _resolve_order(item.order_code)
    collection = None
    if item.collection_id:
        collection = BizCollection.query.get(item.collection_id)
    if not collection:
        collection = BizCollection.query.filter_by(order_id=order.id).first()
    payload = item.to_dict()
    payload.update(
        {
            "patient_code": order.patient_code,
            "patient_name": order.patient_name,
            "order_status": order.status,
            "collection_status": collection.status if collection else None,
            "pipeline": list(PIPELINE),
            "next_stage": (STAGE_TRANSITIONS.get(item.stage) or (None,))[0],
        }
    )
    if include_history:
        payload["history"] = get_sample_queue_history(item.order_code)
    return payload


def ensure_sample_queue_item(
    order_ref: str,
    *,
    actor: str | None = None,
    location: str | None = None,
    note: str | None = None,
    sync_collection: bool = True,
) -> dict[str, Any]:
    """Enter sample queue at collected (requires drawn specimen)."""
    order = _resolve_order(order_ref)
    existing = BizSampleQueueItem.query.filter_by(order_id=order.id).first()
    if existing:
        return _serialize_item(existing, order, include_history=True)

    collection = BizCollection.query.filter_by(order_id=order.id).first()
    if not collection:
        raise ReceptionWorkspaceError(
            "Collection job required before sample queue entry"
        )

    # Ensure specimen is collected
    if sync_collection and collection.status not in {
        COLLECTION_COLLECTED,
        COLLECTION_IN_TRANSIT,
        COLLECTION_DELIVERED,
    }:
        try:
            if collection.status == "assigned":
                biz.accept_collection(order.order_code, actor=actor)
                collection = BizCollection.query.filter_by(order_id=order.id).first()
            if collection and collection.status in {"accepted", "assigned"}:
                collection = biz.collect_sample(order.order_code, actor=actor)
        except BusinessEngineError as exc:
            raise ReceptionWorkspaceError(str(exc)) from exc

    collection = BizCollection.query.filter_by(order_id=order.id).first()
    if not collection or collection.status not in {
        COLLECTION_COLLECTED,
        COLLECTION_IN_TRANSIT,
        COLLECTION_DELIVERED,
        "collected",
        "in_transit",
        "delivered",
    }:
        raise ReceptionWorkspaceError(
            "Sample must be collected before entering sample queue"
        )

    # Map existing collection status to initial stage
    stage = STAGE_COLLECTED
    if collection.status in {COLLECTION_IN_TRANSIT, "in_transit"}:
        stage = STAGE_TRANSPORT
    elif collection.status in {COLLECTION_DELIVERED, "delivered"} or order.status == ORDER_LAB_RECEIVED:
        stage = STAGE_RECEIVED

    now = _utcnow()
    item = BizSampleQueueItem(
        order_id=order.id,
        order_code=order.order_code,
        collection_id=collection.id,
        sample_code=collection.sample_code or collection.barcode_value,
        stage=stage,
        collector_name=collection.collector_name,
        location=location or collection.pickup_address or "Reception Desk",
        notes=note,
        collected_at=now if stage == STAGE_COLLECTED else now,
        transport_at=now if stage == STAGE_TRANSPORT else None,
        received_at=now if stage == STAGE_RECEIVED else None,
        updated_by=actor,
        created_at=now,
        updated_at=now,
    )
    db.session.add(item)
    db.session.flush()
    _append_event(
        item,
        event_type="entered",
        from_stage=None,
        to_stage=stage,
        actor=actor,
        note=note or "Entered sample queue",
        location=item.location,
    )
    return _serialize_item(item, order, include_history=True)


def advance_sample_queue(
    order_ref: str,
    *,
    to_stage: str,
    actor: str | None = None,
    note: str | None = None,
    location: str | None = None,
    sync_collection: bool = True,
) -> dict[str, Any]:
    item = get_sample_queue_item(order_ref)
    if not item:
        raise ReceptionWorkspaceError("Order is not on the sample queue")
    target = normalize_stage(to_stage)
    current = normalize_stage(item.stage)
    allowed = STAGE_TRANSITIONS.get(current, ())
    if target not in allowed:
        raise ReceptionWorkspaceError(
            f"Invalid sample queue transition: {current} → {target}"
        )

    order = _resolve_order(item.order_code)
    collection = BizCollection.query.filter_by(order_id=order.id).first()

    # Sync logistics engines on early stages
    if sync_collection and collection:
        try:
            if target == STAGE_TRANSPORT and collection.status == COLLECTION_COLLECTED:
                biz.handover_sample(order.order_code, actor=actor)
            elif target == STAGE_RECEIVED and collection.status == COLLECTION_IN_TRANSIT:
                biz.receive_sample_at_lab(
                    order.order_code,
                    received_by=actor or "Sample Desk",
                    actor=actor,
                )
            elif target == STAGE_LABORATORY:
                from app.reception_workspace.lab_queue_engine import ensure_lab_queue_item

                # Lab intake board — best effort (may already exist from handoff)
                try:
                    ensure_lab_queue_item(
                        order.order_code,
                        laboratory_name="Central Laboratory",
                        actor=actor,
                    )
                except ReceptionWorkspaceError:
                    pass
        except BusinessEngineError as exc:
            raise ReceptionWorkspaceError(str(exc)) from exc

    now = _utcnow()
    item.stage = target
    item.updated_by = actor
    item.updated_at = now
    if location:
        item.location = location
    if target == STAGE_TRANSPORT:
        item.transport_at = now
    elif target == STAGE_RECEIVED:
        item.received_at = now
    elif target == STAGE_SORTING:
        item.sorting_at = now
    elif target == STAGE_LABORATORY:
        item.laboratory_at = now
    elif target == STAGE_COMPLETED:
        item.completed_at = now

    _append_event(
        item,
        event_type="advanced",
        from_stage=current,
        to_stage=target,
        actor=actor,
        note=note,
        location=item.location,
    )
    db.session.flush()
    return _serialize_item(item, order, include_history=True)


def update_sample_tracking(
    order_ref: str,
    *,
    location: str | None = None,
    note: str | None = None,
    actor: str | None = None,
) -> dict[str, Any]:
    item = get_sample_queue_item(order_ref)
    if not item:
        raise ReceptionWorkspaceError("Order is not on the sample queue")
    if location:
        item.location = location
    if note:
        item.notes = note
    item.updated_by = actor
    item.updated_at = _utcnow()
    _append_event(
        item,
        event_type="tracking",
        from_stage=item.stage,
        to_stage=item.stage,
        actor=actor,
        note=note,
        location=location or item.location,
    )
    db.session.flush()
    return _serialize_item(item, include_history=True)


def get_sample_queue_history(order_ref: str, *, limit: int = 100) -> list[dict[str, Any]]:
    rows = (
        BizSampleQueueEvent.query.filter(
            or_(
                BizSampleQueueEvent.order_code == order_ref,
                BizSampleQueueEvent.queue_item_id == order_ref,
            )
        )
        .order_by(BizSampleQueueEvent.created_at.asc())
        .limit(max(1, min(limit, 500)))
        .all()
    )
    return [r.to_dict() for r in rows]


def track_sample(order_ref: str) -> dict[str, Any]:
    """Realtime tracking snapshot for one order."""
    item = get_sample_queue_item(order_ref)
    if not item:
        # Try auto-derive from collection if present
        order = _resolve_order(order_ref)
        collection = BizCollection.query.filter_by(order_id=order.id).first()
        return {
            "order_code": order.order_code,
            "on_queue": False,
            "order_status": order.status,
            "collection_status": collection.status if collection else None,
            "stage": None,
            "history": [],
            "tracked_at": _utcnow().isoformat() + "Z",
        }
    return {
        **_serialize_item(item, include_history=True),
        "on_queue": True,
        "tracked_at": _utcnow().isoformat() + "Z",
    }


def list_sample_queue(
    *,
    stage: str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    query = BizSampleQueueItem.query
    if stage:
        query = query.filter(BizSampleQueueItem.stage == normalize_stage(stage))
    rows = (
        query.order_by(BizSampleQueueItem.updated_at.desc())
        .limit(max(1, min(limit, 500)))
        .all()
    )
    return [_serialize_item(r) for r in rows]


def sample_queue_statistics() -> dict[str, Any]:
    items = BizSampleQueueItem.query.all()
    by_stage = {s: 0 for s in QUEUE_STAGES}
    for row in items:
        by_stage[row.stage] = by_stage.get(row.stage, 0) + 1
    in_transit = by_stage[STAGE_TRANSPORT]
    active = sum(
        by_stage[s]
        for s in (
            STAGE_COLLECTED,
            STAGE_TRANSPORT,
            STAGE_RECEIVED,
            STAGE_SORTING,
            STAGE_LABORATORY,
        )
    )
    return {
        "by_stage": by_stage,
        "total": len(items),
        "active": active,
        "in_transit": in_transit,
        "completed": by_stage[STAGE_COMPLETED],
        "pipeline": list(PIPELINE),
        "stages": list(QUEUE_STAGES),
    }


def _queue_version() -> int:
    rows = BizSampleQueueItem.query.with_entities(
        BizSampleQueueItem.id,
        BizSampleQueueItem.stage,
        BizSampleQueueItem.location,
        BizSampleQueueItem.updated_at,
    ).all()
    events_count = BizSampleQueueEvent.query.count()
    fp = "|".join(
        f"{r.id}:{r.stage}:{r.location or ''}:"
        f"{r.updated_at.isoformat() if r.updated_at else ''}"
        for r in rows
    )
    fp = f"{fp}#{events_count}"
    return int(hashlib.sha256(fp.encode("utf-8")).hexdigest()[:15], 16)


def sample_queue_dashboard(
    *,
    stage: str | None = None,
    version: int | None = None,
    limit: int = 100,
) -> dict[str, Any]:
    items = list_sample_queue(stage=stage, limit=limit)
    stats = sample_queue_statistics()
    current_version = _queue_version()
    changed = version is None or int(version) != current_version
    return {
        "items": items if changed or version is None else items,
        "statistics": stats,
        "refreshed_at": _utcnow().isoformat() + "Z",
        "version": current_version,
        "changed": changed,
        "workflow": list(PIPELINE),
        "transitions": {k: list(v) for k, v in STAGE_TRANSITIONS.items()},
    }


def sample_queue_refresh(*, version: int | None = None) -> dict[str, Any]:
    dash = sample_queue_dashboard(version=version, limit=100)
    return {
        "refreshed_at": dash["refreshed_at"],
        "version": dash["version"],
        "changed": dash["changed"],
        "statistics": dash["statistics"],
        "items": dash["items"] if dash["changed"] or version is None else [],
    }
