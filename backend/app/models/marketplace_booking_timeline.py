from datetime import datetime, timedelta
import uuid

from app.extensions.db import db


class MarketplaceBookingTimeline(db.Model):

    __tablename__ = "marketplace_booking_timelines"

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

    event_type = db.Column(
        db.String(50),
        nullable=False,
    )

    message = db.Column(
        db.Text,
    )

    actor_email = db.Column(
        db.String(255),
        default="SYSTEM",
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
    )

    booking = db.relationship(
        "MarketplaceBooking",
        backref=db.backref(
            "timeline_events",
            lazy=True,
            order_by="MarketplaceBookingTimeline.created_at",
        ),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "booking_id": self.booking_id,
            "event_type": self.event_type,
            "message": self.message,
            "actor_email": self.actor_email,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
