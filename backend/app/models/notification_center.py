from datetime import datetime
import uuid

from app.extensions.db import db


class NCNotification(db.Model):
    __tablename__ = "nc_notifications"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    notification_code = db.Column(db.String(50), unique=True, nullable=False)
    event_type = db.Column(db.String(100))
    channel = db.Column(db.String(50), nullable=False)
    recipient = db.Column(db.String(255), nullable=False)
    subject = db.Column(db.String(255))
    body = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(50), default="QUEUED")
    priority = db.Column(db.String(20), default="NORMAL")
    template_id = db.Column(db.String(36), db.ForeignKey("nc_notification_templates.id"))
    provider_id = db.Column(db.String(36), db.ForeignKey("nc_notification_providers.id"))
    metadata_json = db.Column(db.Text, default="{}")
    latency_ms = db.Column(db.Float, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    sent_at = db.Column(db.DateTime)

    def to_dict(self):
        return {
            "id": self.id,
            "notification_code": self.notification_code,
            "event_type": self.event_type,
            "channel": self.channel,
            "recipient": self.recipient,
            "subject": self.subject,
            "body": self.body,
            "status": self.status,
            "priority": self.priority,
            "template_id": self.template_id,
            "provider_id": self.provider_id,
            "metadata_json": self.metadata_json,
            "latency_ms": self.latency_ms,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
        }


class NCNotificationChannel(db.Model):
    __tablename__ = "nc_notification_channels"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    channel_code = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(255), nullable=False)
    provider_type = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(50), default="ACTIVE")
    config_json = db.Column(db.Text, default="{}")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "channel_code": self.channel_code,
            "name": self.name,
            "provider_type": self.provider_type,
            "status": self.status,
            "config_json": self.config_json,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class NCNotificationTemplate(db.Model):
    __tablename__ = "nc_notification_templates"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    template_code = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(255), nullable=False)
    channel = db.Column(db.String(50), nullable=False)
    language = db.Column(db.String(20), default="vi")
    subject = db.Column(db.String(255))
    body = db.Column(db.Text, nullable=False)
    variables_json = db.Column(db.Text, default="[]")
    status = db.Column(db.String(50), default="ACTIVE")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "template_code": self.template_code,
            "name": self.name,
            "channel": self.channel,
            "language": self.language,
            "subject": self.subject,
            "body": self.body,
            "variables_json": self.variables_json,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class NCNotificationDelivery(db.Model):
    __tablename__ = "nc_notification_deliveries"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    notification_id = db.Column(db.String(36), db.ForeignKey("nc_notifications.id"), nullable=False)
    provider_id = db.Column(db.String(36), db.ForeignKey("nc_notification_providers.id"))
    status = db.Column(db.String(50), default="QUEUED")
    provider_message_id = db.Column(db.String(100))
    error_message = db.Column(db.Text)
    latency_ms = db.Column(db.Float, default=0)
    delivered_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "notification_id": self.notification_id,
            "provider_id": self.provider_id,
            "status": self.status,
            "provider_message_id": self.provider_message_id,
            "error_message": self.error_message,
            "latency_ms": self.latency_ms,
            "delivered_at": self.delivered_at.isoformat() if self.delivered_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class NCNotificationPreference(db.Model):
    __tablename__ = "nc_notification_preferences"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(100), nullable=False, index=True)
    email_enabled = db.Column(db.Boolean, default=True)
    sms_enabled = db.Column(db.Boolean, default=True)
    push_enabled = db.Column(db.Boolean, default=True)
    zalo_enabled = db.Column(db.Boolean, default=True)
    webhook_enabled = db.Column(db.Boolean, default=True)
    mute_start_hour = db.Column(db.Integer)
    mute_end_hour = db.Column(db.Integer)
    critical_override = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "email_enabled": bool(self.email_enabled),
            "sms_enabled": bool(self.sms_enabled),
            "push_enabled": bool(self.push_enabled),
            "zalo_enabled": bool(self.zalo_enabled),
            "webhook_enabled": bool(self.webhook_enabled),
            "mute_start_hour": self.mute_start_hour,
            "mute_end_hour": self.mute_end_hour,
            "critical_override": bool(self.critical_override),
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class NCNotificationProvider(db.Model):
    __tablename__ = "nc_notification_providers"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    provider_code = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(255), nullable=False)
    channel = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(50), default="ACTIVE")
    health_status = db.Column(db.String(50), default="OK")
    config_json = db.Column(db.Text, default="{}")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "provider_code": self.provider_code,
            "name": self.name,
            "channel": self.channel,
            "status": self.status,
            "health_status": self.health_status,
            "config_json": self.config_json,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class NCNotificationRetry(db.Model):
    __tablename__ = "nc_notification_retries"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    notification_id = db.Column(db.String(36), db.ForeignKey("nc_notifications.id"), nullable=False)
    attempt_number = db.Column(db.Integer, default=1)
    status = db.Column(db.String(50), default="RETRY")
    next_retry_at = db.Column(db.DateTime)
    backoff_seconds = db.Column(db.Integer, default=60)
    error_message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "notification_id": self.notification_id,
            "attempt_number": self.attempt_number,
            "status": self.status,
            "next_retry_at": self.next_retry_at.isoformat() if self.next_retry_at else None,
            "backoff_seconds": self.backoff_seconds,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
