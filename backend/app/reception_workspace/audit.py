"""Reception workspace audit helpers."""

from __future__ import annotations

from app.core.audit import write_audit
from app.services.reception_service import log_activity


def write_reception_audit(*, action: str, object_type: str, object_id: str, actor: str | None = None) -> None:
    write_audit(
        action=f"reception.{action}",
        object_type=object_type,
        object_id=str(object_id),
        user_email=actor or "SYSTEM",
    )


def log_reception_activity(
    action: str,
    *,
    patient_id: str | None = None,
    queue_entry_id: str | None = None,
    details: str | None = None,
    actor: str | None = None,
) -> None:
    log_activity(
        action,
        patient_id=patient_id,
        queue_entry_id=queue_entry_id,
        details=details,
        actor_email=actor,
    )
    write_reception_audit(action=action, object_type="reception", object_id=patient_id or queue_entry_id or action, actor=actor)
