from datetime import datetime
import uuid

from app.extensions.db import db


class ColdBoxDevice(db.Model):

    __tablename__ = "cold_box_devices"

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    device_id = db.Column(
        db.String(36),
        db.ForeignKey("iot_devices.id"),
        nullable=False,
        unique=True,
    )

    box_code = db.Column(db.String(50), unique=True, nullable=False)

    capacity_liters = db.Column(db.Float, default=20)

    min_temp_c = db.Column(db.Float, default=2.0)

    max_temp_c = db.Column(db.Float, default=8.0)

    status = db.Column(db.String(20), default="ACTIVE")

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    device = db.relationship("IoTDevice")

    def to_dict(self):
        return {
            "id": self.id,
            "device_id": self.device_id,
            "box_code": self.box_code,
            "capacity_liters": self.capacity_liters,
            "min_temp_c": self.min_temp_c,
            "max_temp_c": self.max_temp_c,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "device": self.device.to_dict() if self.device else None,
        }
