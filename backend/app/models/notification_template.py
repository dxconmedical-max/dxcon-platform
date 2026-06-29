from datetime import datetime
import uuid

from app.extensions.db import db


class NotificationTemplate(db.Model):

    __tablename__ = "notification_templates"

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    template_code = db.Column(db.String(50), unique=True, nullable=False)

    name = db.Column(db.String(255), nullable=False)

    subject = db.Column(db.String(255))

    body = db.Column(db.Text, nullable=False)

    sms_body = db.Column(db.Text)

    push_title = db.Column(db.String(255))

    push_body = db.Column(db.Text)

    zalo_body = db.Column(db.Text)

    default_channels = db.Column(db.String(255), default="IN_APP,EMAIL")

    status = db.Column(db.String(20), default="ACTIVE")

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "template_code": self.template_code,
            "name": self.name,
            "subject": self.subject,
            "body": self.body,
            "sms_body": self.sms_body,
            "push_title": self.push_title,
            "push_body": self.push_body,
            "zalo_body": self.zalo_body,
            "default_channels": self.default_channels,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def channel_list(self):
        return [item.strip() for item in (self.default_channels or "").split(",") if item.strip()]
