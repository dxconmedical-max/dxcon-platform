"""MDM audit helpers."""

from __future__ import annotations

from app.core.audit import write_audit


def write_mdm_audit(
    *,
    action: str,
    entity_type: str,
    entity_id: str,
    actor: str | None = None,
    note: str | None = None,
) -> None:
    detail = f"entity={entity_type}"
    if note:
        detail = f"{detail}; {note}"
    write_audit(
        action=f"mdm.{action}",
        object_type=entity_type,
        object_id=entity_id,
        user_email=actor or "SYSTEM",
    )
