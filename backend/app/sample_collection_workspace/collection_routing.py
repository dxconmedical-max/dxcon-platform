"""Collection routing service — creates and lists by collection_mode."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from app.extensions.db import db
from app.models.biz_order import BizOrder
from app.models.sample_collection import SampleCollection
from app.models.test_catalog import TestCatalog
from app.sample_collection_workspace.collection_domain import (
    DESK_QUEUE_STATUSES,
    FIELD_COLLECTION_MODES,
    FIELD_QUEUE_STATUSES,
    MODE_AT_RECEPTION,
    MODE_HOME_COLLECTION,
    ST_ARRIVED_AT_LAB,
    ST_ASSIGNED,
    ST_CANCELLED,
    ST_COLLECTED,
    ST_IN_TRANSIT,
    ST_REJECTED,
    ST_REQUESTED,
    ST_VERIFIED,
    CollectionDomainError,
    assert_transition,
    infer_legacy_mode,
    is_desk_mode,
    is_field_mode,
    normalize_status,
    validate_mode,
    validate_pickup_details,
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
    if not columns or name in columns:
        kwargs[name] = value


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
    pickup_data = validate_pickup_details(mode, pickup or {})

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
        elif existing.collection_mode and existing.collection_mode != mode:
            # Keep first authoritative mode; do not flip on retry
            pass
        if organization_id and (not columns or "partner_id" in columns) and not existing.partner_id:
            existing.partner_id = organization_id
        if mode == MODE_AT_RECEPTION:
            if not existing.collection_location and (not columns or "collection_location" in columns):
                existing.collection_location = "Reception Desk"
        else:
            for key, value in pickup_data.items():
                if value is not None and (not columns or key in columns):
                    setattr(existing, key, value)
            if pickup_data.get("pickup_address") and (not columns or "collection_location" in columns):
                existing.collection_location = pickup_data["pickup_address"]
            if pickup_data.get("pickup_city") and (not columns or "location_city" in columns):
                existing.location_city = pickup_data["pickup_city"]
        if commit:
            db.session.commit()
        else:
            db.session.flush()
        return existing

    if not order.barcode_value:
        order.barcode_value = f"BC-{order.order_code}"

    kwargs: dict[str, Any] = {
        "order_id": order.id,
        "status": ST_REQUESTED,
    }
    _set(kwargs, columns, "collection_mode", mode)
    _set(kwargs, columns, "marketplace_booking_id", None)
    _set(kwargs, columns, "expected_barcode", order.barcode_value)
    _set(kwargs, columns, "patient_verified", False)
    _set(kwargs, columns, "order_verified", False)
    _set(kwargs, columns, "specimen_type", "BLOOD")
    if organization_id:
        _set(kwargs, columns, "partner_id", organization_id)

    if mode == MODE_AT_RECEPTION:
        _set(kwargs, columns, "collection_location", "Reception Desk")
        _set(kwargs, columns, "collector_name", None)
    else:
        _set(kwargs, columns, "collection_location", pickup_data.get("pickup_address"))
        _set(kwargs, columns, "location_city", pickup_data.get("pickup_city"))
        for key, value in pickup_data.items():
            _set(kwargs, columns, key, value)

    collection = SampleCollection(**kwargs)
    db.session.add(collection)
    try:
        db.session.flush()
    except Exception:
        logger.exception("Failed creating SampleCollection for order %s mode=%s", order.order_code, mode)
        raise
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
    if item["status"] == ST_VERIFIED or (
        item.get("patient_verified") and item.get("order_verified") and item["status"] in {ST_REQUESTED, ST_ASSIGNED}
    ):
        if item.get("patient_verified") and item.get("order_verified"):
            item["status"] = ST_VERIFIED
    item["actionable"] = item["status"] not in TERMINAL
    item["workflow_path"] = workflow_path_for_mode(mode) if mode else "/app/collector/workflow"
    # Stop advertising source=desk as routing; keep for display only
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
        }
    return item


def _enrich_list(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [annotate_collection_payload(row) for row in rows]


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
    field_items = []
    for item in items:
        mode = (item.get("collection_mode") or "").strip().upper()
        if not mode:
            mode, _ = infer_legacy_mode(item)
        if mode not in FIELD_COLLECTION_MODES:
            continue
        if not filters.get("status"):
            if normalize_status(item.get("status")) not in {
                normalize_status(s) for s in FIELD_QUEUE_STATUSES
            } and item.get("status") not in FIELD_QUEUE_STATUSES:
                # list_queue already filtered awaiting; keep
                pass
        field_items.append(annotate_collection_payload({**item, "collection_mode": mode}))

    # Org isolation for collector roles
    role = filters.get("role")
    organization_id = filters.get("organization_id")
    if organization_id and role in {"COLLECTOR", "PARTNER_COLLECTOR", "DRIVER"}:
        field_items = [i for i in field_items if i.get("partner_id") == organization_id]

    return {
        "count": len(field_items),
        "items": field_items,
        "queue": "field_collector",
        "modes": sorted(FIELD_COLLECTION_MODES),
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


# Back-compat aliases used by older modules during transition
def ensure_desk_sample_collection(order, **kwargs):
    """Deprecated: PR #10 bridge. Prefer ensure_collection_for_order(..., AT_RECEPTION)."""
    return ensure_collection_for_order(
        order,
        collection_mode=MODE_AT_RECEPTION,
        organization_id=kwargs.get("organization_id"),
        actor=kwargs.get("actor"),
        commit=kwargs.get("commit", False),
    )
