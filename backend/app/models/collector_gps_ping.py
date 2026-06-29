from datetime import datetime
import uuid

from app.extensions.db import db


class CollectorGpsPing(db.Model):

    __tablename__ = "collector_gps_pings"

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    collector_id = db.Column(db.String(36), db.ForeignKey("drivers.id"), nullable=False)

    route_id = db.Column(db.String(36), db.ForeignKey("collector_routes.id"))

    latitude = db.Column(db.String(50), nullable=False)

    longitude = db.Column(db.String(50), nullable=False)

    speed_kmh = db.Column(db.Float)

    heading = db.Column(db.Float)

    accuracy_m = db.Column(db.Float)

    recorded_at = db.Column(db.DateTime, default=datetime.utcnow)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "collector_id": self.collector_id,
            "route_id": self.route_id,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "speed_kmh": self.speed_kmh,
            "heading": self.heading,
            "accuracy_m": self.accuracy_m,
            "recorded_at": self.recorded_at.isoformat() if self.recorded_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
