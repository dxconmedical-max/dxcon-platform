from datetime import datetime
import uuid

from app.extensions.db import db


class ClinicBooking(db.Model):

    __tablename__ = "clinic_bookings"

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    booking_code = db.Column(db.String(50), unique=True, nullable=False)

    clinic_id = db.Column(db.String(36), nullable=False)

    patient_id = db.Column(
        db.String(36),
        db.ForeignKey("patients.id"),
        nullable=False,
    )

    doctor_id = db.Column(db.String(36))

    service_name = db.Column(db.String(255), nullable=False)

    scheduled_at = db.Column(db.DateTime, nullable=False)

    status = db.Column(db.String(50), default="PENDING")

    notes = db.Column(db.Text)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "booking_code": self.booking_code,
            "clinic_id": self.clinic_id,
            "patient_id": self.patient_id,
            "doctor_id": self.doctor_id,
            "service_name": self.service_name,
            "scheduled_at": self.scheduled_at.isoformat() if self.scheduled_at else None,
            "status": self.status,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
