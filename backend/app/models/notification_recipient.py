from datetime import datetime
import uuid

from app.extensions.db import db


class NotificationRecipient(db.Model):

    __tablename__ = "notification_recipients"

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    notification_id = db.Column(
        db.String(36),
        db.ForeignKey("notifications.id"),
        nullable=False,
    )

    recipient_type = db.Column(db.String(50), default="USER")

    recipient_id = db.Column(db.String(36))

    recipient_name = db.Column(db.String(255))

    email = db.Column(db.String(255))

    phone = db.Column(db.String(30))

    zalo_id = db.Column(db.String(100))

    push_token = db.Column(db.String(255))

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "notification_id": self.notification_id,
            "recipient_type": self.recipient_type,
            "recipient_id": self.recipient_id,
            "recipient_name": self.recipient_name,
            "email": self.email,
            "phone": self.phone,
            "zalo_id": self.zalo_id,
            "push_token": self.push_token,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
