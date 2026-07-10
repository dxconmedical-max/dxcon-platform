"""Operations Center audit helpers."""

from __future__ import annotations

from app.core.audit import write_audit


def write_ops_center_audit(*, action: str, object_type: str, object_id: str, actor: str | None = None) -> None:
    write_audit(
        action=f"ops_center.{action}",
        object_type=object_type,
        object_id=str(object_id),
        user_email=actor or "SYSTEM",
    )
