from datetime import datetime
import uuid

from app.extensions.db import db


class IoTOfflineEventBuffer(db.Model):
    __tablename__ = "iot_offline_event_buffer"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    device_id = db.Column(db.String(36), db.ForeignKey("iot_devices.id"), nullable=False, index=True)
    adapter_type = db.Column(db.String(50), default="GENERIC")
    event_type = db.Column(db.String(50), nullable=False)
    payload_json = db.Column(db.Text, default="{}")
    status = db.Column(db.String(20), default="PENDING", index=True)
    buffered_at = db.Column(db.DateTime, default=datetime.utcnow)
    synced_at = db.Column(db.DateTime)

    def to_dict(self):
        return {
            "id": self.id,
            "device_id": self.device_id,
            "adapter_type": self.adapter_type,
            "event_type": self.event_type,
            "payload_json": self.payload_json,
            "status": self.status,
            "buffered_at": self.buffered_at.isoformat() if self.buffered_at else None,
            "synced_at": self.synced_at.isoformat() if self.synced_at else None,
        }
