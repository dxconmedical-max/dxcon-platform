from app.extensions.db import db
from datetime import datetime
import uuid


class EventLog(db.Model):
    __tablename__ = "event_logs"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    event_type = db.Column(db.String(100), nullable=False)
    object_type = db.Column(db.String(100))
    object_id = db.Column(db.String(100))
    message = db.Column(db.Text)
    severity = db.Column(db.String(50), default="INFO")
    request_id = db.Column(db.String(36))

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "event_type": self.event_type,
            "object_type": self.object_type,
            "object_id": self.object_id,
            "message": self.message,
            "severity": self.severity,
            "request_id": self.request_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
