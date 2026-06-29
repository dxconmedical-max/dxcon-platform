from datetime import datetime
import uuid

from app.extensions.db import db


class Notification(db.Model):

    __tablename__ = "notifications"

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    notification_code = db.Column(db.String(50), unique=True, nullable=False)

    template_code = db.Column(db.String(50), nullable=False)

    subject = db.Column(db.String(255))

    body = db.Column(db.Text, nullable=False)

    status = db.Column(db.String(50), default="PENDING")

    priority = db.Column(db.String(20), default="NORMAL")

    reference_type = db.Column(db.String(50))

    reference_id = db.Column(db.String(36))

    metadata_json = db.Column(db.Text)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    sent_at = db.Column(db.DateTime)

    recipients = db.relationship(
        "NotificationRecipient",
        backref="notification",
        lazy=True,
        cascade="all, delete-orphan",
    )

    deliveries = db.relationship(
        "NotificationDelivery",
        backref="notification",
        lazy=True,
        cascade="all, delete-orphan",
    )

    def to_dict(self, include_recipients=False, include_deliveries=False):
        payload = {
            "id": self.id,
            "notification_code": self.notification_code,
            "template_code": self.template_code,
            "subject": self.subject,
            "body": self.body,
            "status": self.status,
            "priority": self.priority,
            "reference_type": self.reference_type,
            "reference_id": self.reference_id,
            "metadata_json": self.metadata_json,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
        }
        if include_recipients:
            payload["recipients"] = [row.to_dict() for row in self.recipients]
        if include_deliveries:
            payload["deliveries"] = [row.to_dict() for row in self.deliveries]
        return payload
