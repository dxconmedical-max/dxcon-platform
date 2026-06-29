from datetime import datetime
import uuid

from app.extensions.db import db


class PartnerAvailability(db.Model):

    __tablename__ = "partner_availabilities"

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    partner_id = db.Column(
        db.String(36),
        db.ForeignKey("partners.id"),
        nullable=False,
    )

    date = db.Column(
        db.String(20),
        nullable=False,
    )

    maximum_daily_capacity = db.Column(
        db.Integer,
        default=50,
        nullable=False,
    )

    booked_count = db.Column(
        db.Integer,
        default=0,
        nullable=False,
    )

    available_slots = db.Column(
        db.Integer,
        default=50,
        nullable=False,
    )

    next_available_time = db.Column(
        db.String(50),
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
    )

    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    partner = db.relationship(
        "Partner",
        backref=db.backref("availabilities", lazy=True),
    )

    __table_args__ = (
        db.UniqueConstraint("partner_id", "date", name="uq_partner_availability_date"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "partner_id": self.partner_id,
            "date": self.date,
            "maximum_daily_capacity": self.maximum_daily_capacity,
            "booked_count": self.booked_count,
            "available_slots": self.available_slots,
            "next_available_time": self.next_available_time,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
