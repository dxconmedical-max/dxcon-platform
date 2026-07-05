"""Partner foundation audit helpers."""

from __future__ import annotations

from app.core.audit import write_audit


def write_org_audit(*, action: str, object_type: str, object_id: str, actor: str | None = None) -> None:
    write_audit(
        action=f"organization.{action}",
        object_type=object_type,
        object_id=object_id,
        user_email=actor or "SYSTEM",
    )
