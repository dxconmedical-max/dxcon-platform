from datetime import datetime
import uuid

from app.extensions.db import db


class DoctorProfile(db.Model):

    __tablename__ = "doctor_profiles"

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    doctor_id = db.Column(db.String(36), unique=True, nullable=False)

    doctor_code = db.Column(db.String(50), unique=True, nullable=False)

    full_name = db.Column(db.String(255), nullable=False)

    license_number = db.Column(db.String(100))

    email = db.Column(db.String(255))

    phone = db.Column(db.String(30))

    specialty_primary = db.Column(db.String(100))

    favorite_services_json = db.Column(db.Text, default="[]")

    linked_clinics_json = db.Column(db.Text, default="[]")

    bio = db.Column(db.Text)

    status = db.Column(db.String(20), default="ACTIVE")

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    def to_dict(self):
        return {
            "id": self.id,
            "doctor_id": self.doctor_id,
            "doctor_code": self.doctor_code,
            "full_name": self.full_name,
            "license_number": self.license_number,
            "email": self.email,
            "phone": self.phone,
            "specialty_primary": self.specialty_primary,
            "favorite_services_json": self.favorite_services_json,
            "linked_clinics_json": self.linked_clinics_json,
            "bio": self.bio,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
