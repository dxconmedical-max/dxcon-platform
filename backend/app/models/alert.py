from app.extensions.db import db
from datetime import datetime
import uuid


class Alert(db.Model):

    __tablename__ = "alerts"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    alert_code = db.Column(db.String(50), unique=True, nullable=False)

    alert_type = db.Column(db.String(100), nullable=False)

    severity = db.Column(db.String(30), default="MEDIUM")

    source_type = db.Column(db.String(100))
    source_id = db.Column(db.String(100))

    message = db.Column(db.Text)

    status = db.Column(db.String(50), default="OPEN")

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    acknowledged_at = db.Column(db.DateTime)
    resolved_at = db.Column(db.DateTime)

    def to_dict(self):
        return {
            "id": self.id,
            "alert_code": self.alert_code,
            "alert_type": self.alert_type,
            "severity": self.severity,
            "source_type": self.source_type,
            "source_id": self.source_id,
            "message": self.message,
            "status": self.status
        }
