from app.extensions.db import db
from datetime import datetime
import uuid

class AuditLog(db.Model):
    __tablename__ = "audit_logs"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_email = db.Column(db.String(255))
    action = db.Column(db.String(255))
    object_type = db.Column(db.String(100))
    object_id = db.Column(db.String(100))
    ip_address = db.Column(db.String(100))
    request_id = db.Column(db.String(36))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "user_email": self.user_email,
            "action": self.action,
            "object_type": self.object_type,
            "object_id": self.object_id,
            "ip_address": self.ip_address,
            "request_id": self.request_id,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
