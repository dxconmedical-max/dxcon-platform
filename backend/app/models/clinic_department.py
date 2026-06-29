from datetime import datetime
import uuid

from app.extensions.db import db


class ClinicDepartment(db.Model):

    __tablename__ = "clinic_departments"

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    clinic_id = db.Column(db.String(36), nullable=False)

    department_code = db.Column(db.String(50), nullable=False)

    name = db.Column(db.String(255), nullable=False)

    status = db.Column(db.String(20), default="ACTIVE")

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "clinic_id": self.clinic_id,
            "department_code": self.department_code,
            "name": self.name,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
