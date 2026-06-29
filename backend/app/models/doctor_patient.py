from datetime import datetime
import uuid

from app.extensions.db import db


class DoctorPatient(db.Model):

    __tablename__ = "doctor_patients"

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    doctor_id = db.Column(db.String(36), nullable=False)

    patient_id = db.Column(
        db.String(36),
        db.ForeignKey("patients.id"),
        nullable=False,
    )

    relationship_status = db.Column(db.String(50), default="ACTIVE")

    assigned_at = db.Column(db.DateTime, default=datetime.utcnow)

    note = db.Column(db.Text)

    __table_args__ = (
        db.UniqueConstraint("doctor_id", "patient_id", name="uq_doctor_patient"),
    )

    patient = db.relationship("Patient")

    def to_dict(self):
        patient = self.patient.to_dict() if self.patient else {}
        return {
            "id": self.id,
            "doctor_id": self.doctor_id,
            "patient_id": self.patient_id,
            "relationship_status": self.relationship_status,
            "assigned_at": self.assigned_at.isoformat() if self.assigned_at else None,
            "note": self.note,
            "patient": patient,
        }
