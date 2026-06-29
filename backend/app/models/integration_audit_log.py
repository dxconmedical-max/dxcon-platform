from datetime import datetime
import uuid

from app.extensions.db import db


class IntegrationAuditLog(db.Model):

    __tablename__ = "integration_audit_logs"

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    connection_id = db.Column(db.String(36))

    message_id = db.Column(db.String(36))

    action = db.Column(db.String(100), nullable=False)

    detail = db.Column(db.Text)

    actor_email = db.Column(db.String(255), default="SYSTEM")

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "connection_id": self.connection_id,
            "message_id": self.message_id,
            "action": self.action,
            "detail": self.detail,
            "actor_email": self.actor_email,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
