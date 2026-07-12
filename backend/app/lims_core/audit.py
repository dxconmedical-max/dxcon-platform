"""LIMS Core audit logging."""

from __future__ import annotations

from app.core.audit import write_audit


def write_lims_audit(*, action: str, object_type: str, object_id: str, actor: str | None = None) -> None:
    write_audit(
        action=f"lims.{action}",
        object_type=object_type,
        object_id=str(object_id),
        user_email=actor or "SYSTEM",
    )
