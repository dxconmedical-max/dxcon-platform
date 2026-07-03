from app.extensions.db import db
from datetime import datetime


class Patient(db.Model):

    __tablename__ = "patients"

    patient_code = db.Column(
        db.String(50),
        primary_key=True,
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

    @property
    def id(self):
        """Backward-compatible alias; production PK is patient_code."""
        return self.patient_code

    def to_dict(self):
        return {
            "id": self.patient_code,
            "patient_code": self.patient_code,
            "full_name": self.full_name,
            "gender": self.gender,
            "date_of_birth": self.date_of_birth,
            "phone": self.phone,
            "email": self.email,
            "address": self.address,
            "national_id": self.national_id
        }
