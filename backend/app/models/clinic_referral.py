from datetime import datetime
import uuid

from app.extensions.db import db


class ClinicReferral(db.Model):

    __tablename__ = "clinic_referrals"

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    referral_code = db.Column(db.String(50), unique=True, nullable=False)

    clinic_id = db.Column(db.String(36), nullable=False)

    patient_id = db.Column(
        db.String(36),
        db.ForeignKey("patients.id"),
        nullable=False,
    )

    doctor_id = db.Column(db.String(36))

    test_code = db.Column(db.String(50))

    test_name = db.Column(db.String(255), nullable=False)

    status = db.Column(db.String(50), default="PENDING")

    notes = db.Column(db.Text)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "referral_code": self.referral_code,
            "clinic_id": self.clinic_id,
            "patient_id": self.patient_id,
            "doctor_id": self.doctor_id,
            "test_code": self.test_code,
            "test_name": self.test_name,
            "status": self.status,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
