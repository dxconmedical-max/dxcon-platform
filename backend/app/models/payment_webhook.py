from datetime import datetime
import uuid

from app.extensions.db import db


class PaymentWebhook(db.Model):

    __tablename__ = "payment_webhooks"

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    provider = db.Column(db.String(50), nullable=False)

    event_type = db.Column(db.String(100), nullable=False)

    payload_json = db.Column(db.Text, default="{}")

    processed = db.Column(db.Boolean, default=False)

    received_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "provider": self.provider,
            "event_type": self.event_type,
            "payload_json": self.payload_json,
            "processed": self.processed,
            "received_at": self.received_at.isoformat() if self.received_at else None,
        }
