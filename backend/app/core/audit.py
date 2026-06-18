from app.extensions.db import db
from app.models.audit_log import AuditLog

def write_audit(
    action,
    entity_type,
    entity_id,
    actor="SYSTEM",
    details=""
):
    log = AuditLog(
        actor=actor,
        action=action,
        entity_type=entity_type,
        entity_id=str(entity_id),
        details=details
    )

    db.session.add(log)
    db.session.flush()

    return log
