from datetime import datetime
import uuid

from app.extensions.db import db


class DoctorNote(db.Model):

    __tablename__ = "doctor_notes"

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

    lab_result_id = db.Column(db.String(36))

    note_text = db.Column(db.Text, nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "doctor_id": self.doctor_id,
            "patient_id": self.patient_id,
            "lab_result_id": self.lab_result_id,
            "note_text": self.note_text,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
