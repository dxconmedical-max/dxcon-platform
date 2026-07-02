from datetime import datetime
import uuid

from app.extensions.db import db


class WebhookIdempotencyKey(db.Model):
    __tablename__ = "webhook_idempotency_keys"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    idempotency_key = db.Column(db.String(128), unique=True, nullable=False, index=True)
    webhook_id = db.Column(db.String(36), index=True)
    delivery_id = db.Column(db.String(36))
    response_json = db.Column(db.Text, default="{}")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "idempotency_key": self.idempotency_key,
            "webhook_id": self.webhook_id,
            "delivery_id": self.delivery_id,
            "response_json": self.response_json,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class WebhookReplayLog(db.Model):
    __tablename__ = "webhook_replay_logs"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    delivery_id = db.Column(db.String(36), nullable=False, index=True)
    replay_token = db.Column(db.String(64), unique=True, nullable=False)
    status = db.Column(db.String(50), default="COMPLETED")
    detail_json = db.Column(db.Text, default="{}")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "delivery_id": self.delivery_id,
            "replay_token": self.replay_token,
            "status": self.status,
            "detail_json": self.detail_json,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
