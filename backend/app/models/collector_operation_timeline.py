from datetime import datetime
import uuid

from app.extensions.db import db


class CollectorOperationTimeline(db.Model):

    __tablename__ = "collector_operation_timelines"

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    collector_id = db.Column(db.String(36), db.ForeignKey("drivers.id"), nullable=False)

    route_id = db.Column(db.String(36), db.ForeignKey("collector_routes.id"))

    booking_id = db.Column(db.String(36), db.ForeignKey("marketplace_bookings.id"))

    event_type = db.Column(db.String(100), nullable=False)

    message = db.Column(db.Text)

    actor_email = db.Column(db.String(255), default="SYSTEM")

    metadata_json = db.Column(db.Text)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "collector_id": self.collector_id,
            "route_id": self.route_id,
            "booking_id": self.booking_id,
            "event_type": self.event_type,
            "message": self.message,
            "actor_email": self.actor_email,
            "metadata_json": self.metadata_json,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
