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
        db.String(50),
        db.ForeignKey("patients.patient_code"),
        nullable=False,
    )

    lab_result_id = db.Column(db.String(36))

    note_text = db.Column(db.Text, nullable=False)

    note_type = db.Column(db.String(50), default="clinical")
    visibility = db.Column(db.String(30), default="internal")
    order_code = db.Column(db.String(50))
    report_code = db.Column(db.String(50))
    follow_up_recommendation = db.Column(db.Text)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "doctor_id": self.doctor_id,
            "patient_id": self.patient_id,
            "lab_result_id": self.lab_result_id,
            "note_text": self.note_text,
            "note_type": getattr(self, "note_type", None) or "clinical",
            "visibility": getattr(self, "visibility", None) or "internal",
            "order_code": getattr(self, "order_code", None),
            "report_code": getattr(self, "report_code", None),
            "follow_up_recommendation": getattr(self, "follow_up_recommendation", None),
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
