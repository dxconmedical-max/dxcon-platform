from datetime import datetime
import uuid

from app.extensions.db import db


class GPSReading(db.Model):

    __tablename__ = "gps_readings"

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    device_id = db.Column(
        db.String(36),
        db.ForeignKey("iot_devices.id"),
        nullable=False,
    )

    latitude = db.Column(db.Float, nullable=False)

    longitude = db.Column(db.Float, nullable=False)

    recorded_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "device_id": self.device_id,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "recorded_at": self.recorded_at.isoformat() if self.recorded_at else None,
        }
