from datetime import datetime
import uuid

from app.extensions.db import db


class PatientPreference(db.Model):

    __tablename__ = "patient_preferences"

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

    pref_key = db.Column(db.String(100), nullable=False)

    pref_value = db.Column(db.Text)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    __table_args__ = (
        db.UniqueConstraint("patient_id", "pref_key", name="uq_patient_pref"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "patient_id": self.patient_id,
            "pref_key": self.pref_key,
            "pref_value": self.pref_value,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
