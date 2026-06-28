from datetime import datetime
import uuid

from app.extensions.db import db


class CollectorCheckEvent(db.Model):

    __tablename__ = "collector_check_events"

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    collector_id = db.Column(db.String(36), db.ForeignKey("drivers.id"), nullable=False)

    route_id = db.Column(db.String(36), db.ForeignKey("collector_routes.id"))

    booking_id = db.Column(db.String(36), db.ForeignKey("marketplace_bookings.id"))

    event_type = db.Column(db.String(50), nullable=False)

    latitude = db.Column(db.String(50))

    longitude = db.Column(db.String(50))

    note = db.Column(db.Text)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "collector_id": self.collector_id,
            "route_id": self.route_id,
            "booking_id": self.booking_id,
            "event_type": self.event_type,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "note": self.note,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
