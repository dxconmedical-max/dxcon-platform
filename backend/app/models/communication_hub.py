from datetime import datetime
import uuid

from app.extensions.db import db


class WorkflowAutomationEvent(db.Model):
    __tablename__ = "workflow_automation_events"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    event_code = db.Column(db.String(50), unique=True, nullable=False)
    event_type = db.Column(db.String(50), nullable=False)
    source_type = db.Column(db.String(50))
    source_id = db.Column(db.String(36))
    payload_json = db.Column(db.Text, default="{}")
    status = db.Column(db.String(50), default="RECEIVED")
    processed_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "event_code": self.event_code,
            "event_type": self.event_type,
            "source_type": self.source_type,
            "source_id": self.source_id,
            "payload_json": self.payload_json,
            "status": self.status,
            "processed_at": self.processed_at.isoformat() if self.processed_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class WebhookEndpoint(db.Model):
    __tablename__ = "webhook_endpoints"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    webhook_code = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(255), nullable=False)
    target_url = db.Column(db.String(500), nullable=False)
    secret = db.Column(db.String(255))
    event_types_json = db.Column(db.Text, default="[]")
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "webhook_code": self.webhook_code,
            "name": self.name,
            "target_url": self.target_url,
            "secret": self.secret,
            "event_types_json": self.event_types_json,
            "is_active": bool(self.is_active),
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class WebhookDeliveryLog(db.Model):
    __tablename__ = "webhook_delivery_logs"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    webhook_id = db.Column(db.String(36), db.ForeignKey("webhook_endpoints.id"))
    event_type = db.Column(db.String(50))
    payload_json = db.Column(db.Text, default="{}")
    status = db.Column(db.String(50), default="PENDING")
    response_code = db.Column(db.Integer)
    error_message = db.Column(db.Text)
    delivered_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "webhook_id": self.webhook_id,
            "event_type": self.event_type,
            "payload_json": self.payload_json,
            "status": self.status,
            "response_code": self.response_code,
            "error_message": self.error_message,
            "delivered_at": self.delivered_at.isoformat() if self.delivered_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class CommunicationQueueItem(db.Model):
    __tablename__ = "communication_queue_items"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    queue_code = db.Column(db.String(50), unique=True, nullable=False)
    channel = db.Column(db.String(50), nullable=False)
    template_code = db.Column(db.String(50))
    recipient = db.Column(db.String(255))
    payload_json = db.Column(db.Text, default="{}")
    status = db.Column(db.String(50), default="PENDING")
    retry_count = db.Column(db.Integer, default=0)
    max_retries = db.Column(db.Integer, default=3)
    next_retry_at = db.Column(db.DateTime)
    notification_id = db.Column(db.String(36))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    processed_at = db.Column(db.DateTime)

    def to_dict(self):
        return {
            "id": self.id,
            "queue_code": self.queue_code,
            "channel": self.channel,
            "template_code": self.template_code,
            "recipient": self.recipient,
            "payload_json": self.payload_json,
            "status": self.status,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "next_retry_at": self.next_retry_at.isoformat() if self.next_retry_at else None,
            "notification_id": self.notification_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "processed_at": self.processed_at.isoformat() if self.processed_at else None,
        }


class CommunicationDeadLetter(db.Model):
    __tablename__ = "communication_dead_letters"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    dead_letter_code = db.Column(db.String(50), unique=True, nullable=False)
    queue_item_id = db.Column(db.String(36))
    channel = db.Column(db.String(50))
    reason = db.Column(db.Text)
    payload_json = db.Column(db.Text, default="{}")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "dead_letter_code": self.dead_letter_code,
            "queue_item_id": self.queue_item_id,
            "channel": self.channel,
            "reason": self.reason,
            "payload_json": self.payload_json,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class CommunicationDeliveryTrack(db.Model):
    __tablename__ = "communication_delivery_tracks"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    track_code = db.Column(db.String(50), unique=True, nullable=False)
    queue_item_id = db.Column(db.String(36))
    notification_id = db.Column(db.String(36))
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
            "track_code": self.track_code,
            "queue_item_id": self.queue_item_id,
            "notification_id": self.notification_id,
            "channel": self.channel,
            "status": self.status,
            "provider_message_id": self.provider_message_id,
            "error_message": self.error_message,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "delivered_at": self.delivered_at.isoformat() if self.delivered_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
