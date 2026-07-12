"""Workflow transition engine — immutable history, server-side validation."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from app.core.statuses import CLINICAL_REPORT_TRANSITIONS, CLINICAL_RESULT_TRANSITIONS
from app.extensions.db import db
from app.models.clinical_governance import ClinicalWorkflowTransition

TRANSITION_MAPS = {
    "result": CLINICAL_RESULT_TRANSITIONS,
    "report": CLINICAL_REPORT_TRANSITIONS,
}


class WorkflowError(ValueError):
    pass


def record_transition(
    *,
    organization_id: str,
    aggregate_type: str,
    aggregate_id: str,
    from_status: str | None,
    to_status: str,
    actor: str,
    reason: str | None = None,
    correlation_id: str | None = None,
    exceptional: bool = False,
) -> ClinicalWorkflowTransition:
    if to_status == "RELEASED" and aggregate_type == "result":
        raise WorkflowError("Result release requires explicit release workflow action")
    transitions = TRANSITION_MAPS.get(aggregate_type, {})
    if transitions and from_status is not None:
        allowed = transitions.get(from_status, set())
        if to_status not in allowed and not exceptional:
            raise WorkflowError(f"Invalid transition {from_status} -> {to_status}")
    if exceptional and not reason:
        raise WorkflowError("Reason required for exceptional transition")
    row = ClinicalWorkflowTransition(
        organization_id=organization_id,
        aggregate_type=aggregate_type,
        aggregate_id=aggregate_id,
        from_status=from_status,
        to_status=to_status,
        actor=actor,
        reason=reason,
        correlation_id=correlation_id or uuid.uuid4().hex,
    )
    db.session.add(row)
    return row


def timeline(*, organization_id: str, aggregate_type: str, aggregate_id: str) -> list[dict[str, Any]]:
    rows = (
        ClinicalWorkflowTransition.query.filter_by(
            organization_id=organization_id,
            aggregate_type=aggregate_type,
            aggregate_id=aggregate_id,
        )
        .order_by(ClinicalWorkflowTransition.created_at.asc())
        .all()
    )
    return [r.to_dict() for r in rows]
