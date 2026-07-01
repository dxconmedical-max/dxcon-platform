import logging

from app.core.audit import write_audit
from app.core.request_context import get_correlation_id, get_request_id

audit_logger = logging.getLogger("dxcon.audit")


def log_audit_event(
    action,
    object_type,
    object_id,
    user_email="SYSTEM",
    ip_address="",
    request_id=None,
    correlation_id=None,
):
    request_id = request_id or get_request_id()
    correlation_id = correlation_id or get_correlation_id()

    audit_logger.info(
        "audit event",
        extra={
            "action": action,
            "object_type": object_type,
            "object_id": str(object_id),
            "user_email": user_email,
            "ip_address": ip_address,
            "request_id": request_id,
            "correlation_id": correlation_id,
        },
    )

    return write_audit(
        action=action,
        object_type=object_type,
        object_id=object_id,
        user_email=user_email,
        ip_address=ip_address,
        request_id=request_id,
    )
