from datetime import datetime
import uuid

from app.extensions.db import db


class ClinicPatient(db.Model):

    __tablename__ = "clinic_patients"

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    clinic_id = db.Column(db.String(36), nullable=False)

    patient_id = db.Column(
        db.String(36),
        db.ForeignKey("patients.id"),
        nullable=False,
    )

    status = db.Column(db.String(20), default="ACTIVE")

    registered_at = db.Column(db.DateTime, default=datetime.utcnow)

    note = db.Column(db.Text)

    __table_args__ = (
        db.UniqueConstraint("clinic_id", "patient_id", name="uq_clinic_patient"),
    )

    patient = db.relationship("Patient")

    def to_dict(self):
        patient = self.patient.to_dict() if self.patient else {}
        return {
            "id": self.id,
            "clinic_id": self.clinic_id,
            "patient_id": self.patient_id,
            "status": self.status,
            "registered_at": self.registered_at.isoformat() if self.registered_at else None,
            "note": self.note,
            "patient": patient,
        }
