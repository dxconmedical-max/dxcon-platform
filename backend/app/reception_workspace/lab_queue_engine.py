"""Reception Laboratory Queue — post barcode handoff board.

Pipeline: paid → barcode → lab_queue → waiting → processing → completed → verified
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import or_

from app.extensions.db import db
from app.models.biz_order import BizCollection, BizLabQueueItem, BizOrder
from app.reception_workspace.audit import write_reception_audit
from app.reception_workspace.errors import ReceptionWorkspaceError

STAGE_WAITING = "waiting"
STAGE_PROCESSING = "processing"
STAGE_COMPLETED = "completed"
STAGE_VERIFIED = "verified"

QUEUE_STAGES = (STAGE_WAITING, STAGE_PROCESSING, STAGE_COMPLETED, STAGE_VERIFIED)

STAGE_TRANSITIONS: dict[str, tuple[str, ...]] = {
    STAGE_WAITING: (STAGE_PROCESSING,),
    STAGE_PROCESSING: (STAGE_COMPLETED,),
    STAGE_COMPLETED: (STAGE_VERIFIED,),
    STAGE_VERIFIED: (),
}

PRIORITY_URGENT = "urgent"
PRIORITY_HIGH = "high"
PRIORITY_ROUTINE = "routine"
PRIORITY_LOW = "low"

PRIORITIES = (PRIORITY_URGENT, PRIORITY_HIGH, PRIORITY_ROUTINE, PRIORITY_LOW)
PRIORITY_RANK = {
    PRIORITY_URGENT: 0,
    PRIORITY_HIGH: 1,
    PRIORITY_ROUTINE: 2,
    PRIORITY_LOW: 3,
}

PIPELINE = ("paid", "barcode", "lab_queue", "waiting", "processing", "completed", "verified")


def _utcnow() -> datetime:
    return datetime.utcnow()


def normalize_priority(priority: str | None) -> str:
    raw = (priority or PRIORITY_ROUTINE).strip().lower()
    aliases = {"normal": PRIORITY_ROUTINE, "std": PRIORITY_ROUTINE, "stat": PRIORITY_URGENT}
    raw = aliases.get(raw, raw)
    if raw not in PRIORITIES:
        raise ReceptionWorkspaceError(f"Invalid priority: {priority}")
    return raw


def normalize_stage(stage: str | None) -> str:
    raw = (stage or "").strip().lower()
    if raw not in QUEUE_STAGES:
        raise ReceptionWorkspaceError(f"Invalid lab queue stage: {stage}")
    return raw


def _resolve_order(order_ref: str) -> BizOrder:
    order = BizOrder.query.filter(
        or_(BizOrder.order_code == order_ref, BizOrder.id == order_ref)
    ).first()
    if not order:
        raise ReceptionWorkspaceError("Order not found")
    return order


def get_queue_item(order_ref: str) -> BizLabQueueItem | None:
    return BizLabQueueItem.query.filter(
        or_(BizLabQueueItem.order_code == order_ref, BizLabQueueItem.order_id == order_ref)
    ).first()


def ensure_lab_queue_item(
    order_ref: str,
    *,
    priority: str = PRIORITY_ROUTINE,
    laboratory_name: str | None = None,
    queue_reference: str | None = None,
    actor: str | None = None,
) -> dict[str, Any]:
    """Create or return queue row at waiting after paid + barcode handoff."""
    order = _resolve_order(order_ref)
    existing = BizLabQueueItem.query.filter_by(order_id=order.id).first()
    if existing:
        return _serialize_item(existing, order)

    from app.reception_workspace.service import payment_summary_for_order

    summary = payment_summary_for_order(order)
    collection = BizCollection.query.filter_by(order_id=order.id).first()
    specimen_at_lab = bool(
        collection
        and (collection.status or "").lower() in {"delivered", "lab_received", "received"}
    )
    if (
        not specimen_at_lab
        and summary.get("status") != "paid"
        and (order.status or "").lower()
        not in {
            "paid",
            "sampling",
            "collected",
            "in_transit",
            "lab_received",
            "testing",
            "pending_review",
            "approved",
            "released",
        }
    ):
        raise ReceptionWorkspaceError("Order must be paid before lab queue entry")

    # Barcode readiness (stable identifiers)
    from app.reception_workspace.service import generate_barcodes

    barcodes: dict[str, Any] = {}
    if specimen_at_lab and (order.barcode_value or (collection and collection.barcode_value)):
        barcodes = {
            "order_barcode": order.barcode_value
            or (collection.barcode_value if collection else None)
        }
    else:
        barcodes = generate_barcodes(order.order_code)
    if not barcodes.get("order_barcode"):
        raise ReceptionWorkspaceError("Barcode required before lab queue entry")

    ref = queue_reference
    if not ref and collection:
        ref = (
            collection.accession_number
            or collection.sample_code
            or collection.barcode_value
            or collection.id
        )

    item = BizLabQueueItem(
        order_id=order.id,
        order_code=order.order_code,
        stage=STAGE_WAITING,
        priority=normalize_priority(priority),
        queue_reference=ref,
        laboratory_name=laboratory_name or "Central Laboratory",
        entered_at=_utcnow(),
        updated_by=actor,
    )
    db.session.add(item)
    db.session.flush()
    write_reception_audit(
        action="lab_queue_entered",
        object_type="order",
        object_id=order.order_code,
        actor=actor,
    )
    return _serialize_item(item, order)


def advance_lab_queue(
    order_ref: str,
    *,
    to_stage: str,
    actor: str | None = None,
) -> dict[str, Any]:
    item = get_queue_item(order_ref)
    if not item:
        raise ReceptionWorkspaceError("Order is not on the laboratory queue")
    target = normalize_stage(to_stage)
    current = normalize_stage(item.stage)
    allowed = STAGE_TRANSITIONS.get(current, ())
    if target not in allowed:
        raise ReceptionWorkspaceError(
            f"Invalid lab queue transition: {current} → {target}"
        )
    now = _utcnow()
    item.stage = target
    item.updated_by = actor
    item.updated_at = now
    if target == STAGE_PROCESSING:
        item.started_at = item.started_at or now
    elif target == STAGE_COMPLETED:
        item.completed_at = now
    elif target == STAGE_VERIFIED:
        item.verified_at = now
        item.verified_by = actor
    db.session.flush()
    write_reception_audit(
        action=f"lab_queue_{target}",
        object_type="order",
        object_id=item.order_code,
        actor=actor,
    )
    order = _resolve_order(item.order_code)
    return _serialize_item(item, order)


def set_lab_queue_priority(
    order_ref: str,
    *,
    priority: str,
    actor: str | None = None,
) -> dict[str, Any]:
    item = get_queue_item(order_ref)
    if not item:
        raise ReceptionWorkspaceError("Order is not on the laboratory queue")
    if item.stage == STAGE_VERIFIED:
        raise ReceptionWorkspaceError("Cannot change priority of a verified queue item")
    item.priority = normalize_priority(priority)
    item.updated_by = actor
    item.updated_at = _utcnow()
    db.session.flush()
    write_reception_audit(
        action="lab_queue_priority",
        object_type="order",
        object_id=item.order_code,
        actor=actor,
    )
    return _serialize_item(item, _resolve_order(item.order_code))


def _serialize_item(item: BizLabQueueItem, order: BizOrder | None = None) -> dict[str, Any]:
    order = order or _resolve_order(item.order_code)
    payload = item.to_dict()
    payload.update(
        {
            "patient_code": order.patient_code,
            "patient_name": order.patient_name,
            "order_status": order.status,
            "pipeline_stage": item.stage,
            "priority_rank": PRIORITY_RANK.get(item.priority, 99),
            "tests": [
                {"test_code": i.test_code, "test_name": i.test_name}
                for i in (order.items or [])
            ],
        }
    )
    return payload


def list_lab_queue(
    *,
    stage: str | None = None,
    priority: str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    query = BizLabQueueItem.query
    if stage:
        query = query.filter(BizLabQueueItem.stage == normalize_stage(stage))
    if priority:
        query = query.filter(BizLabQueueItem.priority == normalize_priority(priority))
    rows = query.order_by(BizLabQueueItem.updated_at.desc()).limit(max(1, min(limit, 500))).all()
    items = [_serialize_item(row) for row in rows]
    items.sort(
        key=lambda r: (
            PRIORITY_RANK.get(str(r.get("priority")), 99),
            r.get("entered_at") or "",
        )
    )
    return items


def lab_queue_statistics() -> dict[str, Any]:
    items = BizLabQueueItem.query.all()
    by_stage = {s: 0 for s in QUEUE_STAGES}
    by_priority = {p: 0 for p in PRIORITIES}
    for row in items:
        by_stage[row.stage] = by_stage.get(row.stage, 0) + 1
        by_priority[row.priority] = by_priority.get(row.priority, 0) + 1

    # Funnel precursors: paid with barcode not yet on queue
    from app.reception_workspace.service import payment_summary_for_order
    from app.business_engine.statuses import ORDER_PAID

    barcode_ready = 0
    paid_not_queued = 0
    queued_ids = {r.order_id for r in items}
    for order in BizOrder.query.filter(BizOrder.status == ORDER_PAID).limit(200).all():
        if order.id in queued_ids:
            continue
        summary = payment_summary_for_order(order)
        if summary.get("status") != "paid":
            continue
        paid_not_queued += 1
        if order.barcode_value:
            barcode_ready += 1

    active = by_stage[STAGE_WAITING] + by_stage[STAGE_PROCESSING]
    return {
        "by_stage": by_stage,
        "by_priority": by_priority,
        "total_queued": len(items),
        "active": active,
        "waiting": by_stage[STAGE_WAITING],
        "processing": by_stage[STAGE_PROCESSING],
        "completed": by_stage[STAGE_COMPLETED],
        "verified": by_stage[STAGE_VERIFIED],
        "paid_not_queued": paid_not_queued,
        "barcode_ready_not_queued": barcode_ready,
        "pipeline": list(PIPELINE),
        "priorities": list(PRIORITIES),
        "stages": list(QUEUE_STAGES),
    }


def lab_queue_dashboard(
    *,
    stage: str | None = None,
    priority: str | None = None,
    since: str | None = None,
    version: int | None = None,
    limit: int = 100,
) -> dict[str, Any]:
    """Dashboard payload with version token for realtime polling."""
    import hashlib

    items = list_lab_queue(stage=stage, priority=priority, limit=limit)
    stats = lab_queue_statistics()
    latest = (
        db.session.query(db.func.max(BizLabQueueItem.updated_at)).scalar()
        or db.session.query(db.func.max(BizLabQueueItem.entered_at)).scalar()
    )
    # Fingerprint so same-second advances still bump version (SQLite often 1s resolution)
    fp_rows = BizLabQueueItem.query.with_entities(
        BizLabQueueItem.id,
        BizLabQueueItem.stage,
        BizLabQueueItem.priority,
        BizLabQueueItem.updated_at,
        BizLabQueueItem.verified_at,
    ).all()
    fp = "|".join(
        f"{r.id}:{r.stage}:{r.priority}:"
        f"{r.updated_at.isoformat() if r.updated_at else ''}:"
        f"{r.verified_at.isoformat() if r.verified_at else ''}"
        for r in fp_rows
    )
    current_version = int(hashlib.sha256(fp.encode("utf-8")).hexdigest()[:15], 16)

    changed = True
    if version is not None and int(version) == current_version:
        changed = False
    if since and latest:
        try:
            since_dt = datetime.fromisoformat(since.replace("Z", ""))
            if latest <= since_dt and version is not None and int(version) == current_version:
                changed = False
            elif latest > since_dt:
                changed = True
        except ValueError:
            pass

    return {
        "items": items if changed or version is None else items,
        "statistics": stats,
        "refreshed_at": _utcnow().isoformat() + "Z",
        "version": current_version,
        "changed": changed,
        "workflow": list(PIPELINE),
        "transitions": {k: list(v) for k, v in STAGE_TRANSITIONS.items()},
        "priorities": list(PRIORITIES),
    }


def lab_queue_refresh(*, since: str | None = None, version: int | None = None) -> dict[str, Any]:
    """Lightweight poll endpoint for realtime refresh."""
    dash = lab_queue_dashboard(since=since, version=version, limit=100)
    return {
        "refreshed_at": dash["refreshed_at"],
        "version": dash["version"],
        "changed": dash["changed"],
        "statistics": dash["statistics"],
        "items": dash["items"] if dash["changed"] or version is None else [],
    }
