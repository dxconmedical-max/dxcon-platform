from datetime import datetime
import uuid

from app.extensions.db import db


class DoctorAvailability(db.Model):

    __tablename__ = "doctor_availabilities"

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    doctor_id = db.Column(db.String(36), nullable=False)

    day_of_week = db.Column(db.String(20), nullable=False)

    start_time = db.Column(db.String(10), nullable=False)

    end_time = db.Column(db.String(10), nullable=False)

    location = db.Column(db.String(255))

    is_active = db.Column(db.Boolean, default=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "doctor_id": self.doctor_id,
            "day_of_week": self.day_of_week,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "location": self.location,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
