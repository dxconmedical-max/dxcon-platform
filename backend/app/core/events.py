from app.extensions.db import db
from app.models.event_log import EventLog


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


def write_event(
    event_type,
    object_type=None,
    object_id=None,
    message=None,
    severity="INFO",
    request_id=None,
):
    item = EventLog(
        event_type=event_type,
        object_type=object_type,
        object_id=str(object_id) if object_id else None,
        message=message,
        severity=severity,
        request_id=request_id or _current_request_id(),
    )

    db.session.add(item)
    return item
