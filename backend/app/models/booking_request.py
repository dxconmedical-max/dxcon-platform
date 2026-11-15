from datetime import datetime
import uuid

from app.extensions.db import db


class BookingRequest(db.Model):
    """A sample-collection booking request submitted from the public /book page.

    Deliberately holds contact + scheduling details only. No health data, no test names:
    reception calls the person back and records the order inside the normal workflow.
    """

    __tablename__ = "public_booking_requests"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    reference = db.Column(db.String(20), unique=True, nullable=False)
    full_name = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(120))
    address = db.Column(db.String(300), nullable=False)
    district = db.Column(db.String(100))
    preferred_date = db.Column(db.String(10))  # YYYY-MM-DD
    preferred_slot = db.Column(db.String(20), default="ANYTIME")  # MORNING / AFTERNOON / ANYTIME
    note = db.Column(db.String(500))
    consent_contact = db.Column(db.Boolean, nullable=False, default=False)
    consent_version = db.Column(db.String(20))
    consent_at = db.Column(db.DateTime)
    ip_address = db.Column(db.String(50), index=True)
    status = db.Column(db.String(20), nullable=False, default="NEW", index=True)
    handled_by = db.Column(db.String(120))
    handled_at = db.Column(db.DateTime)
    internal_note = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    def to_dict(self):
        return {
            "id": self.id,
            "reference": self.reference,
            "full_name": self.full_name,
            "phone": self.phone,
            "email": self.email,
            "address": self.address,
            "district": self.district,
            "preferred_date": self.preferred_date,
            "preferred_slot": self.preferred_slot,
            "note": self.note,
            "consent_version": self.consent_version,
            "consent_at": self.consent_at.isoformat() if self.consent_at else None,
            "status": self.status,
            "handled_by": self.handled_by,
            "handled_at": self.handled_at.isoformat() if self.handled_at else None,
            "internal_note": self.internal_note,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
