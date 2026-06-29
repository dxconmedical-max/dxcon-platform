from datetime import datetime
import uuid

from app.extensions.db import db


class NotificationDelivery(db.Model):

    __tablename__ = "notification_deliveries"

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

    recipient_id = db.Column(
        db.String(36),
        db.ForeignKey("notification_recipients.id"),
    )

    channel = db.Column(db.String(50), nullable=False)

    status = db.Column(db.String(50), default="PENDING")

    provider_message_id = db.Column(db.String(100))

    error_message = db.Column(db.Text)

    sent_at = db.Column(db.DateTime)

    delivered_at = db.Column(db.DateTime)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "notification_id": self.notification_id,
            "recipient_id": self.recipient_id,
            "channel": self.channel,
            "status": self.status,
            "provider_message_id": self.provider_message_id,
            "error_message": self.error_message,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "delivered_at": self.delivered_at.isoformat() if self.delivered_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
