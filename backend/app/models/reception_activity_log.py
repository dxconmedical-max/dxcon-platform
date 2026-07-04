from __future__ import annotations

from datetime import datetime
import uuid

from app.extensions.db import db


class ReceptionActivityLog(db.Model):
    __tablename__ = "reception_activity_logs"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    action = db.Column(db.String(50), nullable=False, index=True)
    patient_id = db.Column(db.String(50), index=True)
    queue_entry_id = db.Column(db.String(36), index=True)
    details = db.Column(db.Text)
    actor_email = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "action": self.action,
            "patient_id": self.patient_id,
            "queue_entry_id": self.queue_entry_id,
            "details": self.details,
            "actor_email": self.actor_email,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
