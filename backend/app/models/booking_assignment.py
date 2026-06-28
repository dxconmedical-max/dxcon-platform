from datetime import datetime
import uuid

from app.extensions.db import db


class BookingAssignment(db.Model):

    __tablename__ = "booking_assignments"

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    booking_id = db.Column(
        db.String(36),
        db.ForeignKey("marketplace_bookings.id"),
        nullable=False,
    )

    collector_id = db.Column(
        db.String(36),
    )

    partner_id = db.Column(
        db.String(36),
        db.ForeignKey("partners.id"),
        nullable=False,
    )

    scheduled_slot_id = db.Column(
        db.String(36),
        db.ForeignKey("scheduling_slots.id"),
    )

    assignment_status = db.Column(
        db.String(50),
        default="PENDING",
        nullable=False,
    )

    assigned_at = db.Column(
        db.DateTime,
    )

    accepted_at = db.Column(
        db.DateTime,
    )

    note = db.Column(
        db.Text,
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

    booking = db.relationship(
        "MarketplaceBooking",
        backref=db.backref("assignments", lazy=True),
    )

    scheduled_slot = db.relationship("SchedulingSlot")

    def to_dict(self):
        return {
            "id": self.id,
            "booking_id": self.booking_id,
            "collector_id": self.collector_id,
            "partner_id": self.partner_id,
            "scheduled_slot_id": self.scheduled_slot_id,
            "assignment_status": self.assignment_status,
            "assigned_at": self.assigned_at.isoformat() if self.assigned_at else None,
            "accepted_at": self.accepted_at.isoformat() if self.accepted_at else None,
            "note": self.note,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
