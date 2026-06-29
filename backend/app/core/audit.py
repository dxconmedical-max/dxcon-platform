from app.extensions.db import db
from app.models.audit_log import AuditLog


def _current_request_id():
    try:
        from flask import g, has_request_context, request

        if has_request_context():
            if getattr(g, "request_id", None):
                return g.request_id
            header_name = "X-Request-ID"
            return request.headers.get(header_name)
    except RuntimeError:
        pass
    return None


def write_audit(
    action,
    object_type,
    object_id,
    user_email="SYSTEM",
    ip_address="",
    request_id=None,
):
    log = AuditLog(
        user_email=user_email,
        action=action,
        object_type=object_type,
        object_id=str(object_id),
        ip_address=ip_address,
        request_id=request_id or _current_request_id(),
    )

    db.session.add(log)
    return log
