"""Integration audit — Epic 3.5."""

from __future__ import annotations

import json
from typing import Any

from app.extensions.db import db
from app.integration.models import IntgAuditEvent


def write_integration_audit(
    *,
    action: str,
    actor: str | None = None,
    organization_id: str | None = None,
    connector_id: str | None = None,
    message_id: str | None = None,
    correlation_id: str | None = None,
    outcome: str = "SUCCESS",
    detail: dict[str, Any] | None = None,
) -> dict:
    row = IntgAuditEvent(
        action=action,
        actor=actor or "SYSTEM",
        organization_id=organization_id,
        connector_id=connector_id,
        message_id=message_id,
        correlation_id=correlation_id,
        outcome=outcome,
        detail_json=json.dumps(detail or {}),
    )
    db.session.add(row)
    db.session.flush()
    return row.to_dict()
