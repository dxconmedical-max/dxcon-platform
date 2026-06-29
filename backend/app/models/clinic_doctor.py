from datetime import datetime
import uuid

from app.extensions.db import db


class ClinicDoctor(db.Model):

    __tablename__ = "clinic_doctors"

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    clinic_id = db.Column(db.String(36), nullable=False)

    doctor_id = db.Column(db.String(36), nullable=False)

    department_id = db.Column(db.String(36))

    role = db.Column(db.String(50), default="STAFF")

    status = db.Column(db.String(20), default="ACTIVE")

    joined_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint("clinic_id", "doctor_id", name="uq_clinic_doctor"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "clinic_id": self.clinic_id,
            "doctor_id": self.doctor_id,
            "department_id": self.department_id,
            "role": self.role,
            "status": self.status,
            "joined_at": self.joined_at.isoformat() if self.joined_at else None,
        }
