from datetime import datetime
import uuid

from app.extensions.db import db


class IoTDevice(db.Model):

    __tablename__ = "iot_devices"

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    device_code = db.Column(db.String(50), unique=True, nullable=False)

    device_type = db.Column(db.String(50), default="COLD_BOX")

    serial_number = db.Column(db.String(100))

    partner_id = db.Column(db.String(36))

    status = db.Column(db.String(20), default="ACTIVE")

    last_seen_at = db.Column(db.DateTime)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "device_code": self.device_code,
            "device_type": self.device_type,
            "serial_number": self.serial_number,
            "partner_id": self.partner_id,
            "status": self.status,
            "last_seen_at": self.last_seen_at.isoformat() if self.last_seen_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
