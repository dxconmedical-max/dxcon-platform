from datetime import datetime
import uuid

from app.extensions.db import db


class NotificationPreference(db.Model):

    __tablename__ = "notification_preferences"

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    user_id = db.Column(db.String(36), nullable=False)

    channel = db.Column(db.String(50), nullable=False)

    template_code = db.Column(db.String(50))

    is_enabled = db.Column(db.Boolean, default=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    __table_args__ = (
        db.UniqueConstraint("user_id", "channel", "template_code", name="uq_notification_pref"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "channel": self.channel,
            "template_code": self.template_code,
            "is_enabled": self.is_enabled,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
