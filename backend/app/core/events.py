from app.extensions.db import db
from app.models.event_log import EventLog


def write_event(
    event_type,
    object_type=None,
    object_id=None,
    message=None,
    severity="INFO"
):
    item = EventLog(
        event_type=event_type,
        object_type=object_type,
        object_id=str(object_id) if object_id else None,
        message=message,
        severity=severity
    )

    db.session.add(item)
    return item
