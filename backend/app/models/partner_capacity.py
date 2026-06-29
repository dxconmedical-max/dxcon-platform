from datetime import datetime
import uuid

from app.extensions.db import db


class PartnerCapacity(db.Model):

    __tablename__ = "partner_capacities"

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

    service_type = db.Column(
        db.String(50),
        default="COLLECTION",
        nullable=False,
    )

    maximum_capacity = db.Column(
        db.Integer,
        default=20,
        nullable=False,
    )

    booked_count = db.Column(
        db.Integer,
        default=0,
        nullable=False,
    )

    remaining_capacity = db.Column(
        db.Integer,
        default=20,
        nullable=False,
    )

    note = db.Column(
        db.Text,
    )

    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    partner = db.relationship(
        "Partner",
        backref=db.backref("capacities", lazy=True),
    )

    __table_args__ = (
        db.UniqueConstraint(
            "partner_id",
            "date",
            "service_type",
            name="uq_partner_capacity_day_service",
        ),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "partner_id": self.partner_id,
            "date": self.date,
            "service_type": self.service_type,
            "maximum_capacity": self.maximum_capacity,
            "booked_count": self.booked_count,
            "remaining_capacity": self.remaining_capacity,
            "note": self.note,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
