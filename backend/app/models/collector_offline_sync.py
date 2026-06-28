from datetime import datetime
import uuid

from app.extensions.db import db


class CollectorOfflineSync(db.Model):

    __tablename__ = "collector_offline_syncs"

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    collector_id = db.Column(db.String(36), db.ForeignKey("drivers.id"), nullable=False)

    client_event_id = db.Column(db.String(100), nullable=False)

    event_type = db.Column(db.String(100), nullable=False)

    payload_json = db.Column(db.Text, nullable=False)

    status = db.Column(db.String(50), default="PENDING")

    error_message = db.Column(db.Text)

    client_recorded_at = db.Column(db.DateTime)

    synced_at = db.Column(db.DateTime)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "collector_id": self.collector_id,
            "client_event_id": self.client_event_id,
            "event_type": self.event_type,
            "payload_json": self.payload_json,
            "status": self.status,
            "error_message": self.error_message,
            "client_recorded_at": (
                self.client_recorded_at.isoformat() if self.client_recorded_at else None
            ),
            "synced_at": self.synced_at.isoformat() if self.synced_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
