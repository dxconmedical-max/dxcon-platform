from datetime import datetime
import uuid

from app.extensions.db import db


class TemperatureReading(db.Model):

    __tablename__ = "temperature_readings"

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

    cold_box_id = db.Column(db.String(36))

    celsius = db.Column(db.Float, nullable=False)

    recorded_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "device_id": self.device_id,
            "cold_box_id": self.cold_box_id,
            "celsius": self.celsius,
            "recorded_at": self.recorded_at.isoformat() if self.recorded_at else None,
        }
