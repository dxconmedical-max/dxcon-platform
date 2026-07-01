from datetime import datetime
import uuid

from app.extensions.db import db


class IntegrationPluginState(db.Model):
    __tablename__ = "integration_plugin_states"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    plugin_id = db.Column(db.String(100), unique=True, nullable=False)
    name = db.Column(db.String(255), nullable=False)
    version = db.Column(db.String(50), default="1.0.0")
    status = db.Column(db.String(50), default="DISABLED")
    config_json = db.Column(db.Text, default="{}")
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "plugin_id": self.plugin_id,
            "name": self.name,
            "version": self.version,
            "status": self.status,
            "config_json": self.config_json,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class IntegrationDomainEvent(db.Model):
    __tablename__ = "integration_domain_events"

    id = db.Column(db.String(36), primary_key=True)
    event_code = db.Column(db.String(50), unique=True, nullable=False)
    event_type = db.Column(db.String(100), nullable=False, index=True)
    source = db.Column(db.String(100), default="dxcon")
    correlation_id = db.Column(db.String(100))
    payload_json = db.Column(db.Text, default="{}")
    status = db.Column(db.String(50), default="PUBLISHED")
    published_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "event_code": self.event_code,
            "event_type": self.event_type,
            "source": self.source,
            "correlation_id": self.correlation_id,
            "payload_json": self.payload_json,
            "status": self.status,
            "published_at": self.published_at.isoformat() if self.published_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class IntegrationEventDeliveryLog(db.Model):
    __tablename__ = "integration_event_delivery_logs"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    event_id = db.Column(db.String(36), nullable=False, index=True)
    handler_name = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(50), default="OK")
    detail_json = db.Column(db.Text, default="{}")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "event_id": self.event_id,
            "handler_name": self.handler_name,
            "status": self.status,
            "detail_json": self.detail_json,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class WebhookEndpoint(db.Model):
    __tablename__ = "integration_webhook_endpoints"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    endpoint_code = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(255), nullable=False)
    target_url = db.Column(db.String(500), nullable=False)
    event_types_json = db.Column(db.Text, default="[]")
    status = db.Column(db.String(50), default="ACTIVE")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "endpoint_code": self.endpoint_code,
            "name": self.name,
            "target_url": self.target_url,
            "event_types_json": self.event_types_json,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class WebhookSecret(db.Model):
    __tablename__ = "integration_webhook_secrets"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    webhook_id = db.Column(db.String(36), db.ForeignKey("integration_webhook_endpoints.id"), nullable=False)
    secret_value = db.Column(db.String(255), nullable=False)
    algorithm = db.Column(db.String(50), default="HMAC-SHA256")
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "webhook_id": self.webhook_id,
            "algorithm": self.algorithm,
            "is_active": bool(self.is_active),
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class WebhookEvent(db.Model):
    __tablename__ = "integration_webhook_events"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    event_code = db.Column(db.String(50), unique=True, nullable=False)
    webhook_id = db.Column(db.String(36), db.ForeignKey("integration_webhook_endpoints.id"))
    event_type = db.Column(db.String(100), nullable=False)
    payload_json = db.Column(db.Text, default="{}")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "event_code": self.event_code,
            "webhook_id": self.webhook_id,
            "event_type": self.event_type,
            "payload_json": self.payload_json,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class WebhookDelivery(db.Model):
    __tablename__ = "integration_webhook_deliveries"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    delivery_code = db.Column(db.String(50), unique=True, nullable=False)
    webhook_id = db.Column(db.String(36), db.ForeignKey("integration_webhook_endpoints.id"), nullable=False)
    webhook_event_id = db.Column(db.String(36), db.ForeignKey("integration_webhook_events.id"))
    event_type = db.Column(db.String(100))
    payload_json = db.Column(db.Text, default="{}")
    signature = db.Column(db.String(255))
    status = db.Column(db.String(50), default="PENDING")
    response_code = db.Column(db.Integer)
    failure_reason = db.Column(db.Text)
    attempt_count = db.Column(db.Integer, default=0)
    max_retries = db.Column(db.Integer, default=3)
    delivered_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "delivery_code": self.delivery_code,
            "webhook_id": self.webhook_id,
            "webhook_event_id": self.webhook_event_id,
            "event_type": self.event_type,
            "payload_json": self.payload_json,
            "signature": self.signature,
            "status": self.status,
            "response_code": self.response_code,
            "failure_reason": self.failure_reason,
            "attempt_count": self.attempt_count,
            "max_retries": self.max_retries,
            "delivered_at": self.delivered_at.isoformat() if self.delivered_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class IntegrationJob(db.Model):
    __tablename__ = "integration_jobs"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    job_code = db.Column(db.String(50), unique=True, nullable=False)
    adapter_type = db.Column(db.String(50), nullable=False)
    direction = db.Column(db.String(20), default="OUTBOUND")
    payload_json = db.Column(db.Text, default="{}")
    status = db.Column(db.String(50), default="PENDING")
    retry_count = db.Column(db.Integer, default=0)
    max_retries = db.Column(db.Integer, default=3)
    last_error = db.Column(db.Text)
    processed_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "job_code": self.job_code,
            "adapter_type": self.adapter_type,
            "direction": self.direction,
            "payload_json": self.payload_json,
            "status": self.status,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "last_error": self.last_error,
            "processed_at": self.processed_at.isoformat() if self.processed_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class IntegrationJobAttempt(db.Model):
    __tablename__ = "integration_job_attempts"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id = db.Column(db.String(36), db.ForeignKey("integration_jobs.id"), nullable=False)
    attempt_number = db.Column(db.Integer, default=1)
    status = db.Column(db.String(50), default="PENDING")
    detail_json = db.Column(db.Text, default="{}")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "job_id": self.job_id,
            "attempt_number": self.attempt_number,
            "status": self.status,
            "detail_json": self.detail_json,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class IntegrationDeadLetter(db.Model):
    __tablename__ = "integration_dead_letters"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id = db.Column(db.String(36), db.ForeignKey("integration_jobs.id"), nullable=False)
    reason = db.Column(db.Text)
    payload_json = db.Column(db.Text, default="{}")
    replayed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "job_id": self.job_id,
            "reason": self.reason,
            "payload_json": self.payload_json,
            "replayed": bool(self.replayed),
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
