from datetime import datetime
import uuid

from app.extensions.db import db


class PatientProfile(db.Model):

    __tablename__ = "patient_profiles"

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    patient_id = db.Column(
        db.String(36),
        db.ForeignKey("patients.id"),
        unique=True,
        nullable=False,
    )

    avatar_url = db.Column(db.String(255))

    language = db.Column(db.String(10), default="vi")

    timezone = db.Column(db.String(50), default="Asia/Ho_Chi_Minh")

    favorite_doctors_json = db.Column(db.Text, default="[]")

    favorite_clinics_json = db.Column(db.Text, default="[]")

    family_members_json = db.Column(db.Text, default="[]")

    qr_code = db.Column(db.String(100), unique=True)

    qr_payload = db.Column(db.String(255))

    emergency_contact_name = db.Column(db.String(255))

    emergency_contact_phone = db.Column(db.String(30))

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    def to_dict(self):
        return {
            "id": self.id,
            "patient_id": self.patient_id,
            "avatar_url": self.avatar_url,
            "language": self.language,
            "timezone": self.timezone,
            "favorite_doctors_json": self.favorite_doctors_json,
            "favorite_clinics_json": self.favorite_clinics_json,
            "family_members_json": self.family_members_json,
            "qr_code": self.qr_code,
            "qr_payload": self.qr_payload,
            "emergency_contact_name": self.emergency_contact_name,
            "emergency_contact_phone": self.emergency_contact_phone,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
