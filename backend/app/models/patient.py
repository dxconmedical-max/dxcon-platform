from app.extensions.db import db
from datetime import datetime
import uuid


class Patient(db.Model):

    __tablename__ = "patients"

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    patient_code = db.Column(
        db.String(50),
        unique=True,
        nullable=False
    )

    full_name = db.Column(
        db.String(255),
        nullable=False
    )

    gender = db.Column(
        db.String(20)
    )

    date_of_birth = db.Column(
        db.String(20)
    )

    phone = db.Column(
        db.String(30)
    )

    email = db.Column(
        db.String(255)
    )

    address = db.Column(
        db.Text
    )

    national_id = db.Column(
        db.String(50)
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    def to_dict(self):
        return {
            "id": self.id,
            "patient_code": self.patient_code,
            "full_name": self.full_name,
            "gender": self.gender,
            "date_of_birth": self.date_of_birth,
            "phone": self.phone,
            "email": self.email,
            "address": self.address,
            "national_id": self.national_id
        }
