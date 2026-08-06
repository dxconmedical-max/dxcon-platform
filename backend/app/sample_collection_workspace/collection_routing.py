"""Collection routing service — creates and lists by collection_mode."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from app.extensions.db import db
from app.models.biz_order import BizOrder
from app.models.sample_collection import SampleCollection
from app.models.sample_tracking import SampleTracking
from app.sample_collection_workspace.collection_domain import (
    COLLECTOR_ACTIVE_QUEUE_STATUSES,
    FIELD_COLLECTION_MODES,
    FIELD_QUEUE_STATUSES,
    FIELD_REQUEST_BOARD_STATUSES,
    HOME_COLLECTOR_QUEUE_MODES,
    MODE_AT_RECEPTION,
    MODE_CLINIC_COLLECTION,
    MODE_HOME_COLLECTION,
    NON_SPECIMEN_SAMPLE_TYPES,
    ST_ARRIVED_AT_LAB,
    ST_ASSIGNED,
    ST_CANCELLED,
    ST_PENDING_ASSIGNMENT,
    ST_REJECTED,
    ST_REQUESTED,
    ST_VERIFIED,
    CollectionDomainError,
    assert_transition,
    infer_legacy_mode,
    initial_status_for_mode,
    is_field_mode,
    normalize_status,
    order_requires_specimen_collection,
    validate_collection_request,
    validate_mode,
    workflow_path_for_mode,
)
from app.services.sample_collection_workflow import SampleCollectionWorkflowService

logger = logging.getLogger("dxcon.collection_routing")

TERMINAL = frozenset({ST_ARRIVED_AT_LAB, ST_CANCELLED, ST_REJECTED, "RECEIVED", "RELEASED", "COMPLETED"})


def _columns() -> set[str]:
    try:
        return set(SampleCollectionWorkflowService._sample_collection_db_columns() or set())
    except Exception:
        return set()


def _set(kwargs: dict[str, Any], columns: set[str], name: str, value: Any) -> None:
    if value is None:
        return
    if not columns or name in columns:
        kwargs[name] = value


def _ensure_sample_tracking(collection: SampleCollection, order: BizOrder) -> SampleTracking:
    if collection.sample_tracking_id:
        existing = SampleTracking.query.get(collection.sample_tracking_id)
        if existing:
            return existing
    code = f"SMP-{order.order_code}" if order and order.order_code else f"SMP-{collection.id[:8].upper()}"
    tracking = SampleTracking.query.filter_by(sample_code=code).first()
    if not tracking:
        tracking = SampleTracking(
            sample_code=code,
            marketplace_booking_id=None,
            collector_id=None,
            status="PENDING",
        )
        db.session.add(tracking)
        db.session.flush()
    collection.sample_tracking_id = tracking.id
    db.session.flush()
    return tracking


def _apply_request_fields(target: Any, mode: str, request_data: dict[str, Any], columns: set[str]) -> None:
    is_dict = isinstance(target, dict)

    def put(name: str, value: Any) -> None:
        if value is None:
            return
        if columns and name not in columns:
            return
        if is_dict:
            target[name] = value
        else:
            setattr(target, name, value)

    put("specimen_type", request_data.get("specimen_type"))
    put("priority", request_data.get("priority"))
    put("collection_request_note", request_data.get("collection_request_note"))
    if request_data.get("collection_request_note"):
        put("notes", request_data.get("collection_request_note"))

    if mode == MODE_AT_RECEPTION:
        put("collection_location", "Reception Desk")
        put("collector_name", None)
        put("collector_id", None)
        return

    put("pickup_address", request_data.get("pickup_address"))
    put("pickup_city", request_data.get("pickup_city"))
    put("pickup_province", request_data.get("pickup_province"))
    put("pickup_district", request_data.get("pickup_district"))
    put("pickup_ward", request_data.get("pickup_ward"))
    put("contact_person", request_data.get("contact_person"))
    put("contact_phone", request_data.get("contact_phone"))
    put("requested_date", request_data.get("requested_date"))
    put("requested_time_window", request_data.get("requested_time_window"))
    put("pickup_latitude", request_data.get("pickup_latitude"))
    put("pickup_longitude", request_data.get("pickup_longitude"))
    put("clinic_name", request_data.get("clinic_name"))
    put("collector_id", None)
    put("collector_name", None)

    if mode == MODE_HOME_COLLECTION:
        put("collection_location", request_data.get("pickup_address"))
        put("location_city", request_data.get("pickup_city"))
    elif mode == MODE_CLINIC_COLLECTION:
        clinic = request_data.get("clinic_name") or request_data.get("pickup_address")
        put("collection_location", clinic)
        put("location_city", request_data.get("pickup_city") or clinic)


def ensure_collection_for_order(
    order: BizOrder,
    *,
    collection_mode: str,
    pickup: dict[str, Any] | None = None,
    organization_id: str | None = None,
    actor: str | None = None,
    commit: bool = False,
) -> SampleCollection | None:
    """Idempotent SampleCollection for a specimen-requiring order + explicit mode."""
    del actor
    if not order_requires_specimen_collection(order):
        return None

    mode = validate_mode(collection_mode)
    request_data = validate_collection_request(mode, pickup or {})
    status = initial_status_for_mode(mode)

    existing = (
        SampleCollection.query.filter_by(order_id=order.id)
        .filter(SampleCollection.status.notin_([ST_REJECTED, ST_CANCELLED, "REJECTED", "CANCELLED"]))
        .order_by(SampleCollection.created_at.desc())
        .first()
    )
    columns = _columns()

    if existing:
        if not getattr(existing, "collection_mode", None) and (not columns or "collection_mode" in columns):
            existing.collection_mode = mode
        if organization_id and (not columns or "partner_id" in columns) and not existing.partner_id:
            existing.partner_id = organization_id
        _apply_request_fields(existing, mode, request_data, columns)
        if not existing.sample_tracking_id:
            _ensure_sample_tracking(existing, order)
        if commit:
            db.session.commit()
        else:
            db.session.flush()
        return existing

    if not order.barcode_value:
        order.barcode_value = f"BC-{order.order_code}"

    kwargs: dict[str, Any] = {
        "order_id": order.id,
        "status": status,
        "collector_id": None,
    }
    _set(kwargs, columns, "collection_mode", mode)
    _set(kwargs, columns, "marketplace_booking_id", None)
    _set(kwargs, columns, "expected_barcode", order.barcode_value)
    _set(kwargs, columns, "patient_verified", False)
    _set(kwargs, columns, "order_verified", False)
    if organization_id:
        _set(kwargs, columns, "partner_id", organization_id)

    _apply_request_fields(kwargs, mode, request_data, columns)

    collection = SampleCollection(**kwargs)
    db.session.add(collection)
    try:
        db.session.flush()
    except Exception:
        logger.exception("Failed creating SampleCollection for order %s mode=%s", order.order_code, mode)
        raise

    _ensure_sample_tracking(collection, order)

    if commit:
        db.session.commit()
    return collection


def _resolve_patient_code_for_home(home) -> str:
    from app.business_engine import service as biz
    from app.business_engine.service import table_has_column
    from app.models.patient import Patient

    raw = str(getattr(home, "patient_id", None) or "").strip()
    if not raw:
        raise CollectionDomainError("HomeCollection.patient_id is required", 400)

    try:
        # HomeCollection.patient_id is typically patients.id (UUID PK in Postgres),
        # while the ORM primary key is patient_code.
        if table_has_column("patients", "id"):
            row = db.session.execute(
                db.text("SELECT patient_code FROM patients WHERE id = :raw LIMIT 1"),
                {"raw": raw},
            ).fetchone()
            if row and row[0]:
                return str(row[0])

        patient = Patient.query.get(raw) or Patient.query.filter_by(patient_code=raw).first()
        if patient:
            return patient.patient_code

        created = biz.create_patient(
            full_name=f"Home Patient {raw[:8]}",
            phone=f"09{raw.replace('-', '')[-8:]}" if len(raw) >= 8 else "0900000000",
            patient_code=raw[:50],
            actor="home_collection_bridge",
        )
        return getattr(created, "patient_code", None) or raw[:50]
    except Exception:
        db.session.rollback()
        # After rollback, re-resolve existing patient if the failure was a collision.
        if table_has_column("patients", "id"):
            row = db.session.execute(
                db.text("SELECT patient_code FROM patients WHERE id = :raw LIMIT 1"),
                {"raw": raw},
            ).fetchone()
            if row and row[0]:
                return str(row[0])
        patient = Patient.query.get(raw) or Patient.query.filter_by(patient_code=raw).first()
        if patient:
            return patient.patient_code
        raise


def ensure_sample_collection_from_home_collection(
    home,
    *,
    actor: str | None = None,
    commit: bool = False,
) -> SampleCollection:
    """Create SampleCollection for a legacy HomeCollection if missing.

    Gap: /api/v1/home-collections and /api/v1/workflow/bookings wrote HomeCollection
    only — Reception Field Requests / Collector Queue read SampleCollection.
    """
    from app.business_engine import service as biz

    # Prefer SampleTracking.home_collection_id link
    tracking = SampleTracking.query.filter_by(home_collection_id=home.id).first()
    if tracking:
        existing = SampleCollection.query.filter_by(sample_tracking_id=tracking.id).first()
        if existing:
            if not existing.collection_mode:
                existing.collection_mode = MODE_HOME_COLLECTION
            if commit:
                db.session.commit()
            return existing

    note_token = f"home_collection_id:{home.id}"
    existing = (
        SampleCollection.query.filter(SampleCollection.notes.ilike(f"%{note_token}%"))
        .order_by(SampleCollection.created_at.desc())
        .first()
    )
    if existing:
        return existing

    patient_code = _resolve_patient_code_for_home(home)
    order = biz.create_order(patient_code=patient_code, actor=actor or "home_collection_bridge")
    try:
        biz.submit_order_for_payment(order.order_code, actor=actor)
    except Exception:
        logger.exception("submit_order_for_payment skipped for home bridge %s", home.id)

    address = (getattr(home, "address", None) or "").strip() or "Home address TBD"
    scheduled = (getattr(home, "scheduled_time", None) or "").strip() or "TBD"
    from datetime import date as date_cls

    pickup = {
        "specimen_type": "BLOOD",
        "pickup_address": address,
        "pickup_province": "Unknown",
        "pickup_district": "Unknown",
        "contact_person": order.patient_name or "Patient",
        "contact_phone": "0000000000",
        "requested_date": scheduled[:10] if len(scheduled) >= 10 and scheduled[0].isdigit() else date_cls.today().isoformat(),
        "requested_time_window": scheduled or "TBD",
        "note": note_token,
    }
    collection = ensure_collection_for_order(
        order,
        collection_mode=MODE_HOME_COLLECTION,
        pickup=pickup,
        actor=actor,
        commit=False,
    )
    if collection is None:
        raise CollectionDomainError("Failed to create SampleCollection for HomeCollection", 500)

    collection.notes = note_token if not collection.notes else f"{collection.notes}\n{note_token}"
    if getattr(home, "collector_id", None):
        collection.collector_id = home.collector_id
        home_status = normalize_status(getattr(home, "status", None))
        if home_status in {ST_ASSIGNED, "ASSIGNED", "assigned"} or home.collector_id:
            if normalize_status(collection.status) in {ST_REQUESTED, ST_PENDING_ASSIGNMENT}:
                collection.status = ST_ASSIGNED

    tracking = _ensure_sample_tracking(collection, order)
    tracking.home_collection_id = home.id
    db.session.flush()
    if commit:
        db.session.commit()
    return collection


def sync_legacy_home_collections_to_sample_collections(*, limit: int = 50) -> int:
    """Backfill SampleCollection for open HomeCollection rows (REQUESTED/ASSIGNED/PENDING)."""
    from app.models.home_collection import HomeCollection

    open_statuses = ("REQUESTED", "PENDING", "ASSIGNED", "assigned", "PENDING_ASSIGNMENT")
    rows = (
        HomeCollection.query.filter(HomeCollection.status.in_(open_statuses))
        .order_by(HomeCollection.created_at.desc())
        .limit(limit)
        .all()
    )
    created = 0
    for home in rows:
        before = SampleCollection.query.count()
        ensure_sample_collection_from_home_collection(home, actor="home_collection_sync")
        after = SampleCollection.query.count()
        if after > before:
            created += 1
    if created:
        db.session.flush()
    return created


def annotate_collection_payload(item: dict[str, Any]) -> dict[str, Any]:
    mode = (item.get("collection_mode") or "").strip().upper() or None
    if not mode:
        inferred, reason = infer_legacy_mode(item)
        mode = inferred
        item["collection_mode_inferred"] = reason
    item["collection_mode"] = mode
    raw = item.get("status")
    item["status_raw"] = raw
    item["status"] = normalize_status(raw)
    if item.get("patient_verified") and item.get("order_verified") and item["status"] in {
        ST_REQUESTED,
        ST_PENDING_ASSIGNMENT,
        ST_ASSIGNED,
        ST_VERIFIED,
    }:
        item["status"] = ST_VERIFIED
    item["actionable"] = item["status"] not in TERMINAL and item["status"] != ST_PENDING_ASSIGNMENT
    unassigned_field = (
        mode in FIELD_COLLECTION_MODES
        and not item.get("collector_id")
        and item["status"] in {ST_REQUESTED, ST_PENDING_ASSIGNMENT, "PENDING"}
    )
    if unassigned_field:
        # Collectors see the job; Reception/dispatcher assigns before check-in.
        item["actionable"] = True
        item["dispatcher_actionable"] = True
    elif item["status"] == ST_PENDING_ASSIGNMENT and mode in FIELD_COLLECTION_MODES:
        item["actionable"] = False
        item["dispatcher_actionable"] = True
    elif mode in FIELD_COLLECTION_MODES and item["status"] == ST_ASSIGNED:
        item["actionable"] = True
        item["dispatcher_actionable"] = False
    item["workflow_path"] = workflow_path_for_mode(mode) if mode else "/app/collector/workflow"
    if mode == MODE_AT_RECEPTION:
        item["source"] = "reception"
    elif mode in FIELD_COLLECTION_MODES:
        item["source"] = "field"
    else:
        item["source"] = "unknown"

    if not item.get("booking"):
        order = item.get("order") or {}
        item["booking"] = {
            "patient_name": order.get("patient_name"),
            "booking_code": order.get("order_code"),
            "patient_address": item.get("pickup_address")
            or item.get("collection_location")
            or order.get("patient_address"),
            "city": item.get("pickup_city") or item.get("location_city"),
            "patient_phone": item.get("contact_phone"),
            "contact_person": item.get("contact_person"),
        }
    return item


def list_field_collector_queue(**filters) -> dict[str, Any]:
    """Default Collector Queue = HOME_COLLECTION jobs in ASSIGNED(+ verified) status.

    Unassigned REQUESTED jobs stay on Reception Field Collection Requests until
    a collector is assigned (REQUESTED → ASSIGNED).
    """
    explicit_status = filters.get("status")
    status_filter = explicit_status or ",".join(sorted(COLLECTOR_ACTIVE_QUEUE_STATUSES))
    items = SampleCollectionWorkflowService.list_queue(
        status=status_filter,
        collector_id=filters.get("collector_id"),
        location=filters.get("location"),
        date_from=filters.get("date_from"),
        date_to=filters.get("date_to"),
        partner_id=filters.get("partner_id"),
        awaiting_only=False,
    )
    mode_filter = filters.get("modes") or HOME_COLLECTOR_QUEUE_MODES
    field_items = []
    for item in items:
        mode = (item.get("collection_mode") or "").strip().upper()
        if not mode:
            mode, _ = infer_legacy_mode(item)
        if mode not in mode_filter:
            continue
        if not explicit_status:
            raw = item.get("status")
            canonical = normalize_status(raw)
            if canonical not in COLLECTOR_ACTIVE_QUEUE_STATUSES and (raw or "") not in COLLECTOR_ACTIVE_QUEUE_STATUSES:
                continue
        field_items.append(annotate_collection_payload({**item, "collection_mode": mode}))

    role = filters.get("role")
    organization_id = filters.get("organization_id")
    if organization_id and role in {"COLLECTOR", "PARTNER_COLLECTOR", "DRIVER"}:
        field_items = [
            i
            for i in field_items
            if not i.get("partner_id") or i.get("partner_id") == organization_id
        ]

    return {
        "count": len(field_items),
        "items": field_items,
        "queue": "field_collector",
        "modes": sorted(mode_filter),
    }


def list_home_field_requests(**filters) -> dict[str, Any]:
    """Reception Field Collection Requests — HOME/CLINIC in REQUESTED (unassigned)."""
    from sqlalchemy import or_

    # Bridge legacy HomeCollection rows that never created SampleCollection.
    try:
        sync_legacy_home_collections_to_sample_collections(limit=50)
    except Exception:
        logger.exception("legacy HomeCollection → SampleCollection sync failed")

    modes = filters.get("modes") or {MODE_HOME_COLLECTION, MODE_CLINIC_COLLECTION}
    q = SampleCollection.query.filter(SampleCollection.collection_mode.in_(list(modes)))
    if filters.get("status"):
        q = q.filter(SampleCollection.status == filters["status"])
    else:
        q = q.filter(SampleCollection.status.in_(list(FIELD_REQUEST_BOARD_STATUSES)))
    partner_id = filters.get("partner_id") or filters.get("organization_id")
    role = filters.get("role")
    if partner_id and role not in {"SUPER_ADMIN", "SYSTEM_ADMIN", "ADMIN", None}:
        q = q.filter(or_(SampleCollection.partner_id == partner_id, SampleCollection.partner_id.is_(None)))
    rows = q.order_by(SampleCollection.created_at.desc()).limit(int(filters.get("limit") or 200)).all()
    items = []
    for row in rows:
        payload = row.to_dict()
        order = BizOrder.query.get(row.order_id)
        if order:
            payload["order"] = {
                "id": order.id,
                "order_code": order.order_code,
                "patient_name": order.patient_name,
                "patient_code": order.patient_code,
            }
        items.append(annotate_collection_payload(payload))
    return {
        "count": len(items),
        "items": items,
        "queue": "field_collection_requests",
        "modes": sorted(modes),
    }


def list_reception_desk_queue(**filters) -> dict[str, Any]:
    """AT_RECEPTION only (Reception desk collections worklist)."""
    items = SampleCollectionWorkflowService.list_queue(
        status=filters.get("status"),
        collector_id=None,
        location=filters.get("location"),
        date_from=filters.get("date_from"),
        date_to=filters.get("date_to"),
        partner_id=filters.get("partner_id"),
        awaiting_only=not bool(filters.get("status")),
    )
    desk_items = []
    for item in items:
        mode = (item.get("collection_mode") or "").strip().upper()
        if not mode:
            mode, _ = infer_legacy_mode(item)
        if mode != MODE_AT_RECEPTION:
            continue
        desk_items.append(annotate_collection_payload({**item, "collection_mode": mode}))

    role = filters.get("role")
    organization_id = filters.get("organization_id")
    if organization_id and role not in {"SUPER_ADMIN", "SYSTEM_ADMIN", "ADMIN"}:
        desk_items = [i for i in desk_items if not i.get("partner_id") or i.get("partner_id") == organization_id]

    return {
        "count": len(desk_items),
        "items": desk_items,
        "queue": "reception_desk",
        "modes": [MODE_AT_RECEPTION],
    }


def apply_status_transition(collection_id: str, target: str, *, actor: str | None = None) -> SampleCollection:
    del actor
    collection = SampleCollection.query.get(collection_id)
    if not collection:
        raise CollectionDomainError("Sample collection not found", 404)
    new_status = assert_transition(collection.status, target)
    collection.status = new_status
    collection.updated_at = datetime.utcnow()
    if new_status == ST_VERIFIED:
        collection.patient_verified = True
        collection.order_verified = True
    db.session.flush()
    return collection


def assign_collector(
    collection_id: str,
    *,
    collector_id: str,
    collector_name: str | None = None,
    actor: str | None = None,
) -> SampleCollection:
    """Assign or reassign a field collector. Updates queue immediately on flush."""
    from app.models.user import User
    from app.core.audit import write_audit

    collection = SampleCollection.query.get(collection_id)
    if not collection:
        raise CollectionDomainError("Sample collection not found", 404)
    if not is_field_mode(collection.collection_mode):
        raise CollectionDomainError("Only HOME/CLINIC collections can be assigned to field collectors", 400)
    cid = (collector_id or "").strip()
    if not cid:
        raise CollectionDomainError("collector_id is required", 400)

    user = User.query.get(cid)
    name = (collector_name or "").strip() or None
    if user:
        name = name or getattr(user, "full_name", None) or user.email or cid
    if not name:
        name = cid

    current = normalize_status(collection.status)
    previous_collector = collection.collector_id
    if current == ST_PENDING_ASSIGNMENT:
        assert_transition(collection.status, ST_ASSIGNED)
        collection.status = ST_ASSIGNED
        action = "COLLECTION_ASSIGNED"
    elif current == ST_ASSIGNED:
        action = "COLLECTION_REASSIGNED"
    elif current in {ST_REQUESTED, "PENDING"}:
        collection.status = ST_ASSIGNED
        action = "COLLECTION_ASSIGNED"
    else:
        raise CollectionDomainError(
            f"Cannot assign collector from status {collection.status}",
            409,
        )

    collection.collector_id = cid
    collection.collector_name = name
    collection.updated_at = datetime.utcnow()
    db.session.flush()
    write_audit(
        action=action,
        object_type="SampleCollection",
        object_id=collection.id,
        user_email=actor,
    )
    return collection


def release_collector_assignment(
    collection_id: str,
    *,
    actor: str | None = None,
) -> SampleCollection:
    """Release assignment → PENDING_ASSIGNMENT; clears collector."""
    from app.core.audit import write_audit

    collection = SampleCollection.query.get(collection_id)
    if not collection:
        raise CollectionDomainError("Sample collection not found", 404)
    if not is_field_mode(collection.collection_mode):
        raise CollectionDomainError("Only HOME/CLINIC collections support assignment release", 400)
    current = normalize_status(collection.status)
    if current not in {ST_ASSIGNED, ST_PENDING_ASSIGNMENT}:
        raise CollectionDomainError(
            f"Cannot release assignment from status {collection.status}",
            409,
        )
    collection.collector_id = None
    collection.collector_name = None
    collection.status = ST_PENDING_ASSIGNMENT
    collection.updated_at = datetime.utcnow()
    db.session.flush()
    write_audit(
        action="COLLECTION_ASSIGNMENT_RELEASED",
        object_type="SampleCollection",
        object_id=collection.id,
        user_email=actor,
    )
    return collection


def list_assignable_collectors(*, organization_id: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
    from app.models.user import User

    del organization_id
    roles = ("COLLECTOR", "PARTNER_COLLECTOR", "DRIVER", "ADMIN", "SUPER_ADMIN")
    q = User.query.filter(User.is_active.is_(True), User.role.in_(roles))
    rows = q.order_by(User.email).limit(limit).all()
    return [
        {
            "id": u.id,
            "email": u.email,
            "role": u.role,
            "full_name": getattr(u, "full_name", None) or u.email,
        }
        for u in rows
    ]


def report_ambiguous_modes(limit: int = 200) -> dict[str, Any]:
    rows = SampleCollection.query.order_by(SampleCollection.created_at.desc()).limit(limit).all()
    ambiguous = []
    mapped = []
    for row in rows:
        mode, reason = infer_legacy_mode(row)
        payload = {
            "id": row.id,
            "order_id": row.order_id,
            "status": row.status,
            "collection_mode": row.collection_mode,
            "inferred": mode,
            "reason": reason,
        }
        if mode is None:
            ambiguous.append(payload)
        else:
            mapped.append(payload)
    return {"ambiguous": ambiguous, "mapped_sample": mapped[:50], "ambiguous_count": len(ambiguous)}


def ensure_desk_sample_collection(order, **kwargs):
    """Deprecated PR #10 bridge. Prefer ensure_collection_for_order(..., AT_RECEPTION)."""
    return ensure_collection_for_order(
        order,
        collection_mode=MODE_AT_RECEPTION,
        pickup={"specimen_type": kwargs.get("specimen_type") or "BLOOD"},
        organization_id=kwargs.get("organization_id"),
        actor=kwargs.get("actor"),
        commit=kwargs.get("commit", False),
    )
