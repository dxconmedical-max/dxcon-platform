"""Collection routing service — creates and lists by collection_mode."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from app.extensions.db import db
from app.models.biz_order import BizOrder
from app.models.sample_collection import SampleCollection
from app.models.sample_tracking import SampleTracking
from app.models.test_catalog import TestCatalog
from app.sample_collection_workspace.collection_domain import (
    FIELD_COLLECTION_MODES,
    FIELD_QUEUE_STATUSES,
    MODE_AT_RECEPTION,
    MODE_CLINIC_COLLECTION,
    MODE_HOME_COLLECTION,
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
    normalize_status,
    validate_collection_request,
    validate_mode,
    workflow_path_for_mode,
)
from app.services.sample_collection_workflow import SampleCollectionWorkflowService

logger = logging.getLogger("dxcon.collection_routing")

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

TERMINAL = frozenset({ST_ARRIVED_AT_LAB, ST_CANCELLED, ST_REJECTED, "RECEIVED", "RELEASED", "COMPLETED"})


def order_requires_specimen_collection(order: BizOrder) -> bool:
    items = list(order.items or [])
    if not items:
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
        return True
    return False


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
    if item["status"] == ST_PENDING_ASSIGNMENT and mode in FIELD_COLLECTION_MODES:
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
    """HOME_COLLECTION + CLINIC_COLLECTION only (default Collector Queue)."""
    items = SampleCollectionWorkflowService.list_queue(
        status=filters.get("status"),
        collector_id=filters.get("collector_id"),
        location=filters.get("location"),
        date_from=filters.get("date_from"),
        date_to=filters.get("date_to"),
        partner_id=filters.get("partner_id"),
        awaiting_only=not bool(filters.get("status")),
    )
    mode_filter = filters.get("modes") or FIELD_COLLECTION_MODES
    field_items = []
    for item in items:
        mode = (item.get("collection_mode") or "").strip().upper()
        if not mode:
            mode, _ = infer_legacy_mode(item)
        if mode not in mode_filter:
            continue
        field_items.append(annotate_collection_payload({**item, "collection_mode": mode}))

    role = filters.get("role")
    organization_id = filters.get("organization_id")
    if organization_id and role in {"COLLECTOR", "PARTNER_COLLECTOR", "DRIVER"}:
        field_items = [i for i in field_items if i.get("partner_id") == organization_id]

    return {
        "count": len(field_items),
        "items": field_items,
        "queue": "field_collector",
        "modes": sorted(mode_filter),
    }


def list_home_field_requests(**filters) -> dict[str, Any]:
    """Reception Field Collection Requests — HOME and CLINIC."""
    from sqlalchemy import or_

    modes = filters.get("modes") or {MODE_HOME_COLLECTION, MODE_CLINIC_COLLECTION}
    q = SampleCollection.query.filter(SampleCollection.collection_mode.in_(list(modes)))
    if filters.get("status"):
        q = q.filter(SampleCollection.status == filters["status"])
    else:
        q = q.filter(
            SampleCollection.status.in_(
                list(FIELD_QUEUE_STATUSES) + [ST_PENDING_ASSIGNMENT, ST_REQUESTED, "PENDING", ST_ASSIGNED]
            )
        )
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
