from app.extensions.db import db
from datetime import datetime
import uuid


class SampleEvent(db.Model):

    __tablename__ = "sample_events"

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    sample_tracking_id = db.Column(
        db.String(36),
        nullable=False
    )

    event_type = db.Column(
        db.String(100),
        nullable=False
    )

    note = db.Column(
        db.Text
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    def to_dict(self):
        return {
            "id": self.id,
            "sample_tracking_id": self.sample_tracking_id,
            "event_type": self.event_type,
            "note": self.note,
            "created_at": self.created_at.isoformat()
        }
