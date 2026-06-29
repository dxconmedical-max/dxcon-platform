from datetime import datetime
import uuid

from app.extensions.db import db


class DoctorFollowUp(db.Model):

    __tablename__ = "doctor_follow_ups"

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    follow_up_code = db.Column(db.String(50), unique=True, nullable=False)

    doctor_id = db.Column(db.String(36), nullable=False)

    patient_id = db.Column(
        db.String(36),
        db.ForeignKey("patients.id"),
        nullable=False,
    )

    follow_up_date = db.Column(db.DateTime, nullable=False)

    status = db.Column(db.String(50), default="PENDING")

    reminder_sent = db.Column(db.Boolean, default=False)

    notes = db.Column(db.Text)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    def to_dict(self):
        return {
            "id": self.id,
            "follow_up_code": self.follow_up_code,
            "doctor_id": self.doctor_id,
            "patient_id": self.patient_id,
            "follow_up_date": self.follow_up_date.isoformat() if self.follow_up_date else None,
            "status": self.status,
            "reminder_sent": self.reminder_sent,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
