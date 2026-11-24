from datetime import datetime
import uuid

from app.extensions.db import db


class DemoRequest(db.Model):
    """A "Book a demo" message from the public landing page (sales lead, not patient data)."""

    __tablename__ = "public_demo_requests"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    reference = db.Column(db.String(20), unique=True, nullable=False)
    full_name = db.Column(db.String(120), nullable=False)
    organization = db.Column(db.String(160))
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20))
    message = db.Column(db.String(1000))
    lang = db.Column(db.String(5), default="vi")
    consent_contact = db.Column(db.Boolean, nullable=False, default=False)
    ip_address = db.Column(db.String(50), index=True)
    status = db.Column(db.String(20), nullable=False, default="NEW", index=True)
    handled_by = db.Column(db.String(120))
    handled_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    def to_dict(self):
        return {
            "id": self.id,
            "reference": self.reference,
            "full_name": self.full_name,
            "organization": self.organization,
            "email": self.email,
            "phone": self.phone,
            "message": self.message,
            "lang": self.lang,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
