from app.extensions.db import db
from app.models.sample_event import SampleEvent

def create_event(sample_tracking_id, event_type, note=None):
    event = SampleEvent(
        sample_tracking_id=sample_tracking_id,
        event_type=event_type,
        note=note
    )

    db.session.add(event)
    db.session.commit()

    return event
