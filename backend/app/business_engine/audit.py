"""Business engine audit logging."""

from __future__ import annotations

from flask import has_request_context, session

from app.core.audit import write_audit
from app.extensions.db import db
from app.models.biz_order import BizWorkflowAudit


def _actor() -> str:
    if has_request_context():
        return session.get("email") or "SYSTEM"
    return "SYSTEM"


def write_biz_audit(
    *,
    action: str,
    entity_type: str,
    entity_id: str,
    old_status: str | None = None,
    new_status: str | None = None,
    note: str | None = None,
    actor: str | None = None,
) -> BizWorkflowAudit:
    actor_email = actor or _actor()
    entry = BizWorkflowAudit(
        actor=actor_email,
        action=action,
        entity_type=entity_type,
        entity_id=str(entity_id),
        old_status=old_status,
        new_status=new_status,
        note=note,
    )
    db.session.add(entry)
    write_audit(
        action=f"biz.{action}",
        object_type=entity_type,
        object_id=entity_id,
        user_email=actor_email,
    )
    return entry
