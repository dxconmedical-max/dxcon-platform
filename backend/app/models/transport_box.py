from app.extensions.db import db
from datetime import datetime
import uuid


class TransportBox(db.Model):

    __tablename__ = "transport_boxes"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    box_code = db.Column(db.String(50), unique=True, nullable=False)

    driver_id = db.Column(db.String(36))

    temperature = db.Column(db.Float, default=4.0)

    battery_level = db.Column(db.Integer, default=100)

    latitude = db.Column(db.String(50))

    longitude = db.Column(db.String(50))

    status = db.Column(db.String(50), default="ONLINE")

    alert_status = db.Column(db.String(50), default="NORMAL")

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

    def update_alert_status(self):
        if self.temperature is not None and self.temperature > 8:
            self.alert_status = "TEMP_HIGH"
        elif self.temperature is not None and self.temperature < 2:
            self.alert_status = "TEMP_LOW"
        elif self.battery_level is not None and self.battery_level < 20:
            self.alert_status = "LOW_BATTERY"
        else:
            self.alert_status = "NORMAL"

    def to_dict(self):
        return {
            "id": self.id,
            "box_code": self.box_code,
            "driver_id": self.driver_id,
            "temperature": self.temperature,
            "battery_level": self.battery_level,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "map_url": self.map_url(),
            "status": self.status,
            "alert_status": self.alert_status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
