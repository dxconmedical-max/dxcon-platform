"""Analyzer integration service — result ingestion, quarantine, worklist."""

from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime
from typing import Any

from app.analyzer_integration.adapters import get_adapter
from app.core.statuses import (
    ANALYZER_ONLINE,
    ANALYZER_PROVISIONING,
    INTEGRATION_MSG_COMPLETED,
    INTEGRATION_MSG_QUARANTINED,
    INTEGRATION_MSG_RECEIVED,
    WORKLIST_QUEUED,
    WORKLIST_SENT,
)
from app.extensions.db import db
from app.models.analyzer_integration import (
    AnalyzerIntegrationMessage,
    AnalyzerPreliminaryResult,
    AnalyzerWorklistItem,
    IntegrationQuarantine,
    IntegrationTestMapping,
)
from app.models.lab_facility import Analyzer


class AnalyzerIntegrationError(ValueError):
    pass


def _utcnow() -> datetime:
    return datetime.utcnow()


def _hash_payload(payload: dict) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()


def register_analyzer(data: dict[str, Any], *, organization_id: str) -> dict:
    code = data.get("analyzer_code") or f"ANZ-{uuid.uuid4().hex[:6].upper()}"
    if Analyzer.query.filter_by(analyzer_code=code).first():
        raise AnalyzerIntegrationError("Analyzer code exists")
    row = Analyzer(
        analyzer_code=code,
        name=data.get("name", code),
        model=data.get("model"),
        manufacturer=data.get("vendor") or data.get("manufacturer"),
        status=data.get("status", ANALYZER_PROVISIONING),
    )
    for attr, key in (
        ("organization_id", "organization_id"),
        ("laboratory_id", "laboratory_id"),
        ("protocol", "protocol"),
        ("serial_number", "serial_number"),
        ("host", "host"),
        ("port", "port"),
    ):
        if hasattr(row, attr):
            setattr(row, attr, data.get(key) if key != "organization_id" else organization_id)
    if hasattr(row, "enabled"):
        row.enabled = data.get("enabled", True)
    db.session.add(row)
    db.session.flush()
    return analyzer_dict(row)


def analyzer_dict(row: Analyzer) -> dict:
    data = row.to_dict()
    for secret in ("host", "port"):
        if secret in data and data[secret]:
            data[secret] = "***"
    return data


def list_analyzers(*, organization_id: str, page: int = 1, per_page: int = 25) -> dict:
    q = Analyzer.query
    if hasattr(Analyzer, "organization_id"):
        q = q.filter(Analyzer.organization_id == organization_id)
    total = q.count()
    rows = q.order_by(Analyzer.created_at.desc()).offset((page - 1) * per_page).limit(per_page).all()
    return {"total": total, "analyzers": [analyzer_dict(r) for r in rows]}


def get_analyzer(analyzer_id: str, *, organization_id: str) -> dict:
    row = Analyzer.query.get(analyzer_id)
    if not row:
        raise AnalyzerIntegrationError("Analyzer not found")
    if hasattr(row, "organization_id") and row.organization_id and row.organization_id != organization_id:
        raise AnalyzerIntegrationError("Tenant isolation violation")
    return analyzer_dict(row)


def analyzer_health(analyzer_id: str, *, organization_id: str) -> dict:
    row = Analyzer.query.get(analyzer_id)
    if not row:
        raise AnalyzerIntegrationError("Analyzer not found")
    protocol = getattr(row, "protocol", None) or "SIMULATOR"
    adapter = get_adapter(protocol)
    try:
        health = adapter.health_check()
    except PermissionError as exc:
        return {"healthy": False, "error": str(exc)}
    if hasattr(row, "last_seen_at"):
        row.last_seen_at = _utcnow()
    return {"analyzer_id": analyzer_id, **health}


def create_test_mapping(data: dict[str, Any], *, organization_id: str, actor: str) -> dict:
    mapping = IntegrationTestMapping(
        organization_id=organization_id,
        mapping_code=data.get("mapping_code") or f"MAP-{uuid.uuid4().hex[:6].upper()}",
        analyzer_test_code=data["analyzer_test_code"],
        dxcon_test_code=data["dxcon_test_code"],
        specimen_type=data.get("specimen_type"),
        unit=data.get("unit"),
        approved_by=actor,
        effective_at=_utcnow(),
    )
    db.session.add(mapping)
    db.session.flush()
    return mapping.to_dict()


def list_test_mappings(*, organization_id: str) -> dict:
    rows = IntegrationTestMapping.query.filter_by(organization_id=organization_id, status="ACTIVE").all()
    return {"count": len(rows), "mappings": [r.to_dict() for r in rows]}


def ingest_result_message(
    payload: dict[str, Any],
    *,
    organization_id: str,
    analyzer_id: str,
    protocol: str = "SIMULATOR",
) -> dict[str, Any]:
    """Safe result ingestion — never auto-releases patient results."""
    msg_hash = _hash_payload(payload)
    if AnalyzerIntegrationMessage.query.filter_by(message_hash=msg_hash).first():
        return {"status": "duplicate", "message_hash": msg_hash}

    adapter = get_adapter(protocol)
    parsed = adapter.parse_result(payload)

    msg = AnalyzerIntegrationMessage(
        organization_id=organization_id,
        analyzer_id=analyzer_id,
        message_type="RESULT",
        protocol=protocol,
        status=INTEGRATION_MSG_RECEIVED,
        message_hash=msg_hash,
        correlation_id=payload.get("correlation_id") or uuid.uuid4().hex,
        external_message_id=payload.get("external_message_id"),
        redacted_summary=f"barcode={parsed.get('specimen_barcode')} test={parsed.get('analyzer_test_code')}",
    )
    db.session.add(msg)
    db.session.flush()

    barcode = parsed.get("specimen_barcode")
    test_code_analyzer = parsed.get("analyzer_test_code")
    if not barcode:
        return _quarantine(msg, organization_id, "UNKNOWN_BARCODE", "Missing specimen barcode", parsed)

    mapping = IntegrationTestMapping.query.filter_by(
        organization_id=organization_id,
        analyzer_test_code=test_code_analyzer,
        status="ACTIVE",
    ).first()
    if not mapping:
        return _quarantine(msg, organization_id, "UNMAPPED_TEST", f"No mapping for {test_code_analyzer}", parsed)

    original = str(parsed.get("value", ""))
    normalized = original
    unit = parsed.get("unit") or mapping.unit
    if unit and mapping.unit and unit != mapping.unit:
        return _quarantine(msg, organization_id, "UNIT_MISMATCH", f"Expected {mapping.unit}, got {unit}", parsed)

    dup = AnalyzerPreliminaryResult.query.filter_by(
        organization_id=organization_id,
        specimen_barcode=barcode,
        test_code=mapping.dxcon_test_code,
        original_value=original,
    ).first()
    if dup:
        return _quarantine(msg, organization_id, "DUPLICATE_RESULT", "Duplicate analyzer result", parsed, duplicate_of=dup.id)

    result = AnalyzerPreliminaryResult(
        organization_id=organization_id,
        analyzer_id=analyzer_id,
        message_id=msg.id,
        specimen_barcode=barcode,
        test_code=mapping.dxcon_test_code,
        original_value=original,
        normalized_value=normalized,
        unit=unit,
        flag=parsed.get("flag"),
        review_status="PENDING_REVIEW",
        auto_released=False,
    )
    db.session.add(result)
    msg.status = INTEGRATION_MSG_COMPLETED
    msg.processed_at = _utcnow()
    db.session.flush()
    return {"status": "preliminary", "result_id": result.id, "review_status": "PENDING_REVIEW", "auto_released": False}


def _quarantine(
    msg: AnalyzerIntegrationMessage,
    organization_id: str,
    reason_code: str,
    detail: str,
    parsed: dict,
    duplicate_of: str | None = None,
) -> dict:
    msg.status = INTEGRATION_MSG_QUARANTINED
    q = IntegrationQuarantine(
        organization_id=organization_id,
        message_id=msg.id,
        reason_code=reason_code,
        reason_detail=detail,
        specimen_barcode=parsed.get("specimen_barcode"),
        analyzer_test_code=parsed.get("analyzer_test_code"),
        original_value=str(parsed.get("value", "")),
    )
    db.session.add(q)
    if duplicate_of:
        dup_result = AnalyzerPreliminaryResult(
            organization_id=organization_id,
            analyzer_id=msg.analyzer_id,
            message_id=msg.id,
            specimen_barcode=parsed.get("specimen_barcode"),
            test_code=parsed.get("analyzer_test_code"),
            original_value=str(parsed.get("value", "")),
            review_status="QUARANTINED",
            auto_released=False,
            duplicate_of=duplicate_of,
        )
        db.session.add(dup_result)
    return {"status": "quarantined", "reason_code": reason_code, "quarantine_id": q.id}


def list_quarantine(*, organization_id: str) -> dict:
    rows = IntegrationQuarantine.query.filter_by(organization_id=organization_id, status="OPEN").all()
    return {"count": len(rows), "items": [r.to_dict() for r in rows]}


def list_preliminary_results(*, organization_id: str, review_status: str | None = None) -> dict:
    q = AnalyzerPreliminaryResult.query.filter_by(organization_id=organization_id)
    if review_status:
        q = q.filter_by(review_status=review_status)
    rows = q.order_by(AnalyzerPreliminaryResult.created_at.desc()).all()
    return {"count": len(rows), "results": [r.to_dict() for r in rows]}


def list_messages(*, organization_id: str, status: str | None = None) -> dict:
    q = AnalyzerIntegrationMessage.query.filter_by(organization_id=organization_id)
    if status:
        q = q.filter_by(status=status)
    rows = q.order_by(AnalyzerIntegrationMessage.received_at.desc()).limit(100).all()
    return {"count": len(rows), "messages": [r.to_dict() for r in rows]}


def create_worklist_item(data: dict[str, Any], *, organization_id: str) -> dict:
    item = AnalyzerWorklistItem(
        organization_id=organization_id,
        analyzer_id=data["analyzer_id"],
        specimen_barcode=data.get("specimen_barcode"),
        order_code=data.get("order_code"),
        test_code=data.get("test_code"),
        status=WORKLIST_QUEUED,
        correlation_id=data.get("correlation_id") or uuid.uuid4().hex,
    )
    db.session.add(item)
    db.session.flush()
    return item.to_dict()


def send_worklist(analyzer_id: str, *, organization_id: str) -> dict:
    items = AnalyzerWorklistItem.query.filter_by(
        organization_id=organization_id, analyzer_id=analyzer_id, status=WORKLIST_QUEUED
    ).all()
    analyzer = Analyzer.query.get(analyzer_id)
    protocol = getattr(analyzer, "protocol", None) or "SIMULATOR"
    adapter = get_adapter(protocol)
    payload = [i.to_dict() for i in items]
    result = adapter.send_worklist(payload)
    now = _utcnow()
    for item in items:
        item.status = WORKLIST_SENT
        item.sent_at = now
    return {"sent": len(items), **result}


def analyzer_dashboard(*, organization_id: str) -> dict:
    analyzers = Analyzer.query
    if hasattr(Analyzer, "organization_id"):
        analyzers = analyzers.filter(Analyzer.organization_id == organization_id)
    online = analyzers.filter(Analyzer.status == ANALYZER_ONLINE).count() if hasattr(Analyzer, "status") else 0
    pending = AnalyzerPreliminaryResult.query.filter_by(organization_id=organization_id, review_status="PENDING_REVIEW").count()
    quarantined = IntegrationQuarantine.query.filter_by(organization_id=organization_id, status="OPEN").count()
    worklist = AnalyzerWorklistItem.query.filter_by(organization_id=organization_id, status=WORKLIST_QUEUED).count()
    return {
        "kpis": {
            "analyzers_online": online,
            "pending_review": pending,
            "quarantine_open": quarantined,
            "worklist_queued": worklist,
        }
    }
