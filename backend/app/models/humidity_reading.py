from datetime import datetime
import uuid

from app.extensions.db import db


class HumidityReading(db.Model):

    __tablename__ = "humidity_readings"

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

    humidity_percent = db.Column(db.Float, nullable=False)

    recorded_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "device_id": self.device_id,
            "humidity_percent": self.humidity_percent,
            "recorded_at": self.recorded_at.isoformat() if self.recorded_at else None,
        }
