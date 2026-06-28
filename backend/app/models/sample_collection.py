from app.extensions.db import db
from datetime import datetime
import uuid


class SampleCollection(db.Model):

    __tablename__ = "sample_collections"

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    order_id = db.Column(
        db.String(36),
        nullable=False
    )

    marketplace_booking_id = db.Column(
        db.String(36),
        db.ForeignKey("marketplace_bookings.id"),
    )

    collector_id = db.Column(
        db.String(36),
    )

    sample_tracking_id = db.Column(
        db.String(36),
    )

    collector_name = db.Column(
        db.String(255)
    )

    status = db.Column(
        db.String(50),
        default="PENDING"
    )

    collected_at = db.Column(
        db.DateTime
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    def to_dict(self):
        return {
            "id": self.id,
            "order_id": self.order_id,
            "marketplace_booking_id": self.marketplace_booking_id,
            "collector_id": self.collector_id,
            "sample_tracking_id": self.sample_tracking_id,
            "collector_name": self.collector_name,
            "status": self.status,
            "collected_at": self.collected_at.isoformat() if self.collected_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
