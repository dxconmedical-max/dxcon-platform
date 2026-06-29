from datetime import datetime
import uuid

from app.extensions.db import db


class PatientDevice(db.Model):

    __tablename__ = "patient_devices"

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    patient_id = db.Column(
        db.String(36),
        db.ForeignKey("patients.id"),
        nullable=False,
    )

    device_type = db.Column(db.String(50), default="MOBILE")

    device_name = db.Column(db.String(255))

    push_token = db.Column(db.String(255))

    last_seen_at = db.Column(db.DateTime, default=datetime.utcnow)

    is_active = db.Column(db.Boolean, default=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "patient_id": self.patient_id,
            "device_type": self.device_type,
            "device_name": self.device_name,
            "push_token": self.push_token,
            "last_seen_at": self.last_seen_at.isoformat() if self.last_seen_at else None,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
