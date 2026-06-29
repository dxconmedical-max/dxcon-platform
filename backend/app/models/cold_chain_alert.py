from datetime import datetime
import uuid

from app.extensions.db import db


class ColdChainAlert(db.Model):

    __tablename__ = "cold_chain_alerts"

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

    alert_code = db.Column(db.String(50), unique=True, nullable=False)

    alert_type = db.Column(db.String(50), nullable=False)

    severity = db.Column(db.String(20), default="HIGH")

    message = db.Column(db.Text)

    status = db.Column(db.String(20), default="OPEN")

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    resolved_at = db.Column(db.DateTime)

    def to_dict(self):
        return {
            "id": self.id,
            "device_id": self.device_id,
            "alert_code": self.alert_code,
            "alert_type": self.alert_type,
            "severity": self.severity,
            "message": self.message,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
        }
