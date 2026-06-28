from app.extensions.db import db
from datetime import datetime
import uuid


class SampleTracking(db.Model):

    __tablename__ = "sample_trackings"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    sample_code = db.Column(db.String(50), unique=True, nullable=False)

    home_collection_id = db.Column(db.String(36))

    marketplace_booking_id = db.Column(
        db.String(36),
        db.ForeignKey("marketplace_bookings.id"),
    )

    medical_order_id = db.Column(
        db.String(36),
        db.ForeignKey("medical_orders.id"),
    )

    medical_sample_id = db.Column(
        db.String(36),
        db.ForeignKey("medical_samples.id"),
    )

    collector_id = db.Column(db.String(36))

    transport_box_id = db.Column(db.String(36))

    latitude = db.Column(db.String(50))

    longitude = db.Column(db.String(50))

    status = db.Column(db.String(50), default="CHECKED_IN")

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    def map_url(self):

        if self.latitude and self.longitude:
            return f"https://maps.google.com/?q={self.latitude},{self.longitude}"

        return None

    def to_dict(self):
        return {
            "id": self.id,
            "sample_code": self.sample_code,
            "home_collection_id": self.home_collection_id,
            "marketplace_booking_id": self.marketplace_booking_id,
            "medical_order_id": self.medical_order_id,
            "medical_sample_id": self.medical_sample_id,
            "collector_id": self.collector_id,
            "transport_box_id": self.transport_box_id,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "map_url": self.map_url(),
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
