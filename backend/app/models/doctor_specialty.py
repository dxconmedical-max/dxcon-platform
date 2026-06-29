from datetime import datetime
import uuid

from app.extensions.db import db


class DoctorSpecialty(db.Model):

    __tablename__ = "doctor_specialties"

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    doctor_id = db.Column(db.String(36), nullable=False)

    specialty_code = db.Column(db.String(50), nullable=False)

    specialty_name = db.Column(db.String(255), nullable=False)

    is_primary = db.Column(db.Boolean, default=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "doctor_id": self.doctor_id,
            "specialty_code": self.specialty_code,
            "specialty_name": self.specialty_name,
            "is_primary": self.is_primary,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
