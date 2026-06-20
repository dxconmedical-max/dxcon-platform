from app.extensions.db import db
from app.models.audit_log import AuditLog


def write_audit(
    action,
    object_type,
    object_id,
    user_email="SYSTEM",
    ip_address=""
):
    log = AuditLog(
        user_email=user_email,
        action=action,
        object_type=object_type,
        object_id=str(object_id),
        ip_address=ip_address
    )

    db.session.add(log)
    return log
