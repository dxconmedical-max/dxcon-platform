"""Integration platform service — Epic 3.5."""

from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timedelta
from typing import Any

from app.extensions.db import db
from app.integration.adapters import get_adapter
from app.integration.audit import write_integration_audit
from app.integration.mappings.canonical import to_canonical_result, validate_canonical, CANONICAL_RESULT_FIELDS
from app.integration.mappings.engine import apply_mapping_rules, preview_mapping, upsert_mapping_rule
from app.integration.models import (
    IntgApiCredential,
    IntgConnector,
    IntgDeadLetter,
    IntgDeliveryAttempt,
    IntgExternalMapping,
    IntgMessage,
    IntgMappingRule,
    IntgWebhookSubscription,
)
from app.integration.security import enforce_organization_access, mask_payload_preview
from app.lab_workspace.lis_service import import_csv, import_json, upsert_connector as upsert_lis_connector
from app.models.lab_lis import LISConnector
from app.models.user import User
from app.partner_foundation.service import ensure_default_organization


class IntegrationError(ValueError):
    pass


def _utcnow() -> datetime:
    return datetime.utcnow()


def _msg_id() -> str:
    return f"MSG-{uuid.uuid4().hex[:12].upper()}"


def _hash_payload(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def upsert_connector(data: dict[str, Any], *, organization_id: str, actor: str | None) -> dict:
    code = (data.get("connector_code") or "").strip()
    name = (data.get("connector_name") or "").strip()
    if not code or not name:
        raise IntegrationError("connector_code and connector_name required")
    row = IntgConnector.query.filter_by(connector_code=code).first()
    is_new = row is None
    if is_new:
        row = IntgConnector(connector_code=code, connector_name=name, organization_id=organization_id)
        db.session.add(row)
    else:
        if row.organization_id != organization_id:
            raise IntegrationError("connector belongs to another organization")
        row.connector_name = name
        row.updated_at = _utcnow()
    for field in (
        "connector_type", "vendor", "protocol", "laboratory_id", "clinic_id", "base_url",
        "direction", "authentication_type", "secret_reference", "status", "environment",
    ):
        if field in data and data[field] is not None:
            setattr(row, field, data[field])
    db.session.flush()

    if row.protocol in {"CSV", "JSON"} and not row.lis_connector_id:
        lis = upsert_lis_connector(
            {
                "connector_code": f"LIS-{code}",
                "connector_name": name,
                "connector_type": "CSV_UPLOAD" if row.protocol == "CSV" else "JSON_UPLOAD",
                "organization_id": organization_id,
                "laboratory_id": row.laboratory_id,
                "status": "active",
            },
            actor=actor,
        )
        row.lis_connector_id = lis["id"]

    write_integration_audit(
        action="connector_created" if is_new else "connector_updated",
        actor=actor,
        organization_id=organization_id,
        connector_id=row.id,
    )
    return row.to_dict()


def list_connectors(*, organization_id: str | None, page: int = 1, per_page: int = 25) -> dict:
    query = IntgConnector.query
    if organization_id:
        query = query.filter_by(organization_id=organization_id)
    total = query.count()
    rows = query.order_by(IntgConnector.connector_code).offset((page - 1) * per_page).limit(per_page).all()
    return {
        "data": [r.to_dict() for r in rows],
        "pagination": {"page": page, "per_page": per_page, "total": total},
    }


def get_connector(connector_id: str, *, organization_id: str) -> dict:
    row = IntgConnector.query.get(connector_id)
    if not row or row.organization_id != organization_id:
        raise IntegrationError("connector not found")
    return row.to_dict()


def set_connector_status(connector_id: str, status: str, *, organization_id: str, actor: str | None) -> dict:
    row = IntgConnector.query.get(connector_id)
    if not row or row.organization_id != organization_id:
        raise IntegrationError("connector not found")
    row.status = status
    row.updated_at = _utcnow()
    action = "connector_activated" if status == "ACTIVE" else "connector_disabled"
    write_integration_audit(action=action, actor=actor, organization_id=organization_id, connector_id=row.id)
    return row.to_dict()


def test_connection(connector_id: str, *, organization_id: str, actor: str | None) -> dict:
    row = IntgConnector.query.get(connector_id)
    if not row or row.organization_id != organization_id:
        raise IntegrationError("connector not found")
    adapter = get_adapter(row.protocol, row.to_dict())
    result = adapter.test_connection()
    row.last_success_at = _utcnow() if result.get("ok") else None
    row.last_failure_at = None if result.get("ok") else _utcnow()
    write_integration_audit(action="connection_tested", actor=actor, organization_id=organization_id, connector_id=row.id, outcome="SUCCESS" if result.get("ok") else "FAILURE")
    return result


def _check_duplicate(connector_id: str, external_id: str | None, message_type: str, payload_hash: str) -> IntgMessage | None:
    if external_id:
        existing = IntgMessage.query.filter_by(
            connector_id=connector_id,
            external_message_id=external_id,
            message_type=message_type,
        ).first()
        if existing:
            return existing
    return IntgMessage.query.filter_by(connector_id=connector_id, payload_hash=payload_hash, message_type=message_type).first()


def receive_message(
    connector_id: str,
    *,
    organization_id: str,
    message_type: str,
    payload: Any,
    payload_format: str,
    external_message_id: str | None = None,
    correlation_id: str | None = None,
    actor: str | None = None,
) -> dict:
    connector = IntgConnector.query.get(connector_id)
    if not connector or connector.organization_id != organization_id:
        raise IntegrationError("connector not found")
    if connector.status not in {"ACTIVE", "DRAFT"}:
        raise IntegrationError("connector not active")

    raw_bytes = json.dumps(payload, sort_keys=True, default=str).encode()
    payload_hash = _hash_payload(raw_bytes)
    duplicate = _check_duplicate(connector_id, external_message_id, message_type, payload_hash)
    if duplicate:
        write_integration_audit(action="message_received", actor=actor, organization_id=organization_id, connector_id=connector_id, message_id=duplicate.id, outcome="DUPLICATE")
        return {**duplicate.to_dict(), "duplicate": True}

    preview = mask_payload_preview(raw_bytes.decode()[:2000])
    message = IntgMessage(
        message_id=_msg_id(),
        connector_id=connector_id,
        organization_id=organization_id,
        direction="INBOUND",
        message_type=message_type,
        external_message_id=external_message_id,
        correlation_id=correlation_id,
        payload_format=payload_format,
        payload_hash=payload_hash,
        status="RECEIVED",
        payload_preview=preview,
    )
    db.session.add(message)
    db.session.flush()

    try:
        mapped = apply_mapping_rules(connector_id, payload if isinstance(payload, dict) else {})
        canonical = to_canonical_result(mapped)
        ok, errors = validate_canonical(canonical, CANONICAL_RESULT_FIELDS)
        if not ok:
            message.status = "EXCEPTION"
            message.error_message = "; ".join(errors)
            write_integration_audit(action="message_rejected", actor=actor, organization_id=organization_id, connector_id=connector_id, message_id=message.id, outcome="FAILURE")
            return message.to_dict()

        ext_test = canonical.get("test_code")
        if ext_test:
            mapping = IntgExternalMapping.query.filter_by(
                connector_id=connector_id, mapping_kind="TEST_CODE", external_code=str(ext_test)
            ).first()
            if mapping and mapping.internal_code:
                canonical["test_code"] = mapping.internal_code
            elif not _test_in_catalog(str(ext_test)):
                _queue_external_mapping(connector_id, organization_id, "TEST_CODE", str(ext_test))
                message.status = "EXCEPTION"
                message.error_code = "UNKNOWN_TEST_CODE"
                message.error_message = "unknown external test code"
                write_integration_audit(action="message_rejected", actor=actor, organization_id=organization_id, connector_id=connector_id, message_id=message.id, outcome="FAILURE")
                return message.to_dict()

        message.status = "STAGED"
        message.processed_at = _utcnow()
        connector.last_success_at = _utcnow()
        write_integration_audit(action="message_processed", actor=actor, organization_id=organization_id, connector_id=connector_id, message_id=message.id)
        message.status = "ACKNOWLEDGED"
        return message.to_dict()
    except Exception as exc:
        message.status = "EXCEPTION"
        message.error_message = str(exc)[:500]
        connector.last_failure_at = _utcnow()
        _maybe_dead_letter(message, str(exc))
        write_integration_audit(action="message_rejected", actor=actor, organization_id=organization_id, connector_id=connector_id, message_id=message.id, outcome="FAILURE")
        return message.to_dict()


def _test_in_catalog(test_code: str) -> bool:
    from app.models.test_catalog import TestCatalog
    return TestCatalog.query.filter_by(code=test_code).first() is not None


def _queue_external_mapping(connector_id: str, organization_id: str, kind: str, external_code: str) -> None:
    existing = IntgExternalMapping.query.filter_by(
        connector_id=connector_id, mapping_kind=kind, external_code=external_code
    ).first()
    if existing:
        return
    db.session.add(
        IntgExternalMapping(
            connector_id=connector_id,
            organization_id=organization_id,
            mapping_kind=kind,
            external_code=external_code,
            status="pending",
        )
    )
    db.session.flush()


def import_csv_via_connector(
    connector_id: str,
    content: bytes,
    *,
    organization_id: str,
    actor: str | None,
    file_name: str = "import.csv",
) -> dict:
    connector = IntgConnector.query.get(connector_id)
    if not connector or connector.organization_id != organization_id:
        raise IntegrationError("connector not found")
    if not connector.lis_connector_id:
        raise IntegrationError("LIS bridge not configured")
    batch = import_csv(content, connector_id=connector.lis_connector_id, file_name=file_name, actor=actor)
    receive_message(
        connector_id,
        organization_id=organization_id,
        message_type="RESULT_FINAL",
        payload={"batch_code": batch.get("batch_code"), "rows": batch.get("total_rows", 0)},
        payload_format="CSV",
        external_message_id=batch.get("batch_code"),
        actor=actor,
    )
    connector.last_success_at = _utcnow()
    return {"batch": batch, "validation_required": True, "auto_release_disabled": True}


def import_json_via_connector(
    connector_id: str,
    payload: Any,
    *,
    organization_id: str,
    actor: str | None,
) -> dict:
    connector = IntgConnector.query.get(connector_id)
    if not connector or connector.organization_id != organization_id:
        raise IntegrationError("connector not found")
    if not connector.lis_connector_id:
        raise IntegrationError("LIS bridge not configured")
    batch = import_json(payload, connector_id=connector.lis_connector_id, actor=actor)
    receive_message(
        connector_id,
        organization_id=organization_id,
        message_type="RESULT_FINAL",
        payload={"batch_code": batch.get("batch_code")},
        payload_format="JSON",
        external_message_id=batch.get("batch_code"),
        actor=actor,
    )
    connector.last_success_at = _utcnow()
    return {"batch": batch, "validation_required": True, "auto_release_disabled": True}


def list_messages(*, organization_id: str, status: str | None = None, page: int = 1, per_page: int = 25) -> dict:
    query = IntgMessage.query.filter_by(organization_id=organization_id)
    if status:
        query = query.filter_by(status=status)
    total = query.count()
    rows = query.order_by(IntgMessage.created_at.desc()).offset((page - 1) * per_page).limit(per_page).all()
    return {"data": [r.to_dict() for r in rows], "pagination": {"page": page, "per_page": per_page, "total": total}}


def list_exceptions(*, organization_id: str) -> list[dict]:
    rows = IntgMessage.query.filter_by(organization_id=organization_id).filter(
        IntgMessage.status.in_(["EXCEPTION", "REJECTED", "DEAD_LETTER"])
    ).order_by(IntgMessage.created_at.desc()).limit(100).all()
    return [r.to_dict() for r in rows]


def retry_message(message_id: str, *, organization_id: str, actor: str | None) -> dict:
    row = IntgMessage.query.filter_by(message_id=message_id, organization_id=organization_id).first()
    if not row:
        raise IntegrationError("message not found")
    row.retry_count += 1
    row.status = "RECEIVED"
    row.error_message = None
    write_integration_audit(action="message_retried", actor=actor, organization_id=organization_id, message_id=row.id)
    return row.to_dict()


def ignore_message(message_id: str, reason: str, *, organization_id: str, actor: str | None) -> dict:
    row = IntgMessage.query.filter_by(message_id=message_id, organization_id=organization_id).first()
    if not row:
        raise IntegrationError("message not found")
    row.status = "REJECTED"
    row.error_message = f"ignored: {reason}"[:500]
    write_integration_audit(action="message_rejected", actor=actor, organization_id=organization_id, message_id=row.id, detail={"reason": reason})
    return row.to_dict()


def _maybe_dead_letter(message: IntgMessage, error: str) -> None:
    if message.retry_count >= 5:
        message.status = "DEAD_LETTER"
        db.session.add(
            IntgDeadLetter(
                message_id=message.id,
                organization_id=message.organization_id,
                connector_id=message.connector_id,
                retry_count=message.retry_count,
                last_error=error[:500],
                status="DEAD_LETTER",
            )
        )
        write_integration_audit(action="message_dead_lettered", message_id=message.id, outcome="FAILURE")


def integration_health(*, organization_id: str | None = None) -> dict:
    query = IntgConnector.query
    if organization_id:
        query = query.filter_by(organization_id=organization_id)
    connectors = query.all()
    active = sum(1 for c in connectors if c.status == "ACTIVE")
    messages = IntgMessage.query
    if organization_id:
        messages = messages.filter_by(organization_id=organization_id)
    total_msgs = messages.count()
    failed = messages.filter(IntgMessage.status.in_(["EXCEPTION", "DEAD_LETTER", "REJECTED"])).count()
    dead_letters = IntgDeadLetter.query
    if organization_id:
        dead_letters = dead_letters.filter_by(organization_id=organization_id)
    return {
        "active_connectors": active,
        "total_connectors": len(connectors),
        "messages_processed": total_msgs,
        "failed_messages": failed,
        "dead_letter_count": dead_letters.count(),
        "success_rate": round((total_msgs - failed) / total_msgs * 100, 1) if total_msgs else 100.0,
        "import_requires_validation": True,
        "auto_release_disabled": True,
    }


def create_api_credential(data: dict[str, Any], *, organization_id: str, actor: str | None) -> dict:
    import secrets
    raw_key = secrets.token_urlsafe(32)
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
    row = IntgApiCredential(
        organization_id=organization_id,
        name=data.get("name", "API Key"),
        credential_type=data.get("credential_type", "API_KEY"),
        key_hash=key_hash,
        scopes_json=json.dumps(data.get("scopes", ["orders.read"])),
    )
    db.session.add(row)
    db.session.flush()
    write_integration_audit(action="api_key_created", actor=actor, organization_id=organization_id)
    result = row.to_dict()
    result["api_key_once"] = raw_key
    return result


def revoke_api_credential(credential_id: str, *, organization_id: str, actor: str | None) -> dict:
    row = IntgApiCredential.query.get(credential_id)
    if not row or row.organization_id != organization_id:
        raise IntegrationError("credential not found")
    row.revoked_at = _utcnow()
    write_integration_audit(action="api_key_revoked", actor=actor, organization_id=organization_id)
    return row.to_dict()
