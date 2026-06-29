from datetime import datetime
import uuid

from app.extensions.db import db


class ClinicProfile(db.Model):

    __tablename__ = "clinic_profiles"

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    clinic_id = db.Column(db.String(36), unique=True, nullable=False)

    clinic_code = db.Column(db.String(50), unique=True, nullable=False)

    name = db.Column(db.String(255), nullable=False)

    legal_name = db.Column(db.String(255))

    tax_code = db.Column(db.String(50))

    email = db.Column(db.String(255))

    phone = db.Column(db.String(30))

    address = db.Column(db.Text)

    partner_id = db.Column(db.String(36))

    settings_json = db.Column(db.Text, default="{}")

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
            "clinic_id": self.clinic_id,
            "clinic_code": self.clinic_code,
            "name": self.name,
            "legal_name": self.legal_name,
            "tax_code": self.tax_code,
            "email": self.email,
            "phone": self.phone,
            "address": self.address,
            "partner_id": self.partner_id,
            "settings_json": self.settings_json,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
