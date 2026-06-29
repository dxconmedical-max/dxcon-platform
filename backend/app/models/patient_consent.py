from datetime import datetime
import uuid

from app.extensions.db import db


class PatientConsent(db.Model):

    __tablename__ = "patient_consents"

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

    consent_type = db.Column(db.String(50), nullable=False)

    consent_version = db.Column(db.String(20), default="1.0")

    status = db.Column(db.String(20), default="GRANTED")

    granted_at = db.Column(db.DateTime, default=datetime.utcnow)

    revoked_at = db.Column(db.DateTime)

    ip_address = db.Column(db.String(50))

    metadata_json = db.Column(db.Text)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "patient_id": self.patient_id,
            "consent_type": self.consent_type,
            "consent_version": self.consent_version,
            "status": self.status,
            "granted_at": self.granted_at.isoformat() if self.granted_at else None,
            "revoked_at": self.revoked_at.isoformat() if self.revoked_at else None,
            "ip_address": self.ip_address,
            "metadata_json": self.metadata_json,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
