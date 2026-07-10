"""Integration platform SQLAlchemy models — Epic 3.5."""

from __future__ import annotations

from datetime import datetime
import json
import uuid

from app.extensions.db import db


def _uuid() -> str:
    return str(uuid.uuid4())


class IntgConnector(db.Model):
    __tablename__ = "intg_connectors"

    id = db.Column(db.String(36), primary_key=True, default=_uuid)
    connector_code = db.Column(db.String(80), unique=True, nullable=False, index=True)
    connector_name = db.Column(db.String(255), nullable=False)
    connector_type = db.Column(db.String(30), nullable=False)
    vendor = db.Column(db.String(100))
    protocol = db.Column(db.String(30), nullable=False)
    organization_id = db.Column(db.String(36), nullable=False, index=True)
    laboratory_id = db.Column(db.String(36))
    clinic_id = db.Column(db.String(36))
    base_url = db.Column(db.String(500))
    direction = db.Column(db.String(20), nullable=False, default="INBOUND")
    authentication_type = db.Column(db.String(30))
    secret_reference = db.Column(db.String(255))
    status = db.Column(db.String(20), nullable=False, default="DRAFT")
    environment = db.Column(db.String(20), default="production")
    lis_connector_id = db.Column(db.String(36))
    last_success_at = db.Column(db.DateTime)
    last_failure_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "connector_code": self.connector_code,
            "connector_name": self.connector_name,
            "connector_type": self.connector_type,
            "vendor": self.vendor,
            "protocol": self.protocol,
            "organization_id": self.organization_id,
            "laboratory_id": self.laboratory_id,
            "clinic_id": self.clinic_id,
            "base_url": self.base_url,
            "direction": self.direction,
            "authentication_type": self.authentication_type,
            "secret_reference": self.secret_reference,
            "status": self.status,
            "environment": self.environment,
            "lis_connector_id": self.lis_connector_id,
            "last_success_at": self.last_success_at.isoformat() if self.last_success_at else None,
            "last_failure_at": self.last_failure_at.isoformat() if self.last_failure_at else None,
        }


class IntgMessage(db.Model):
    __tablename__ = "intg_messages"
    __table_args__ = (
        db.UniqueConstraint("connector_id", "external_message_id", "message_type", name="uq_intg_msg_dedup"),
    )

    id = db.Column(db.String(36), primary_key=True, default=_uuid)
    message_id = db.Column(db.String(80), unique=True, nullable=False)
    connector_id = db.Column(db.String(36), nullable=False, index=True)
    organization_id = db.Column(db.String(36), nullable=False, index=True)
    direction = db.Column(db.String(20), nullable=False)
    message_type = db.Column(db.String(50), nullable=False)
    external_message_id = db.Column(db.String(255))
    correlation_id = db.Column(db.String(255))
    payload_format = db.Column(db.String(20))
    payload_hash = db.Column(db.String(64), index=True)
    status = db.Column(db.String(30), nullable=False, default="RECEIVED")
    received_at = db.Column(db.DateTime, default=datetime.utcnow)
    processed_at = db.Column(db.DateTime)
    retry_count = db.Column(db.Integer, default=0)
    error_code = db.Column(db.String(50))
    error_message = db.Column(db.Text)
    payload_preview = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self, *, mask_payload: bool = True) -> dict:
        return {
            "id": self.id,
            "message_id": self.message_id,
            "connector_id": self.connector_id,
            "organization_id": self.organization_id,
            "direction": self.direction,
            "message_type": self.message_type,
            "external_message_id": self.external_message_id,
            "correlation_id": self.correlation_id,
            "payload_format": self.payload_format,
            "payload_hash": self.payload_hash,
            "status": self.status,
            "received_at": self.received_at.isoformat() if self.received_at else None,
            "processed_at": self.processed_at.isoformat() if self.processed_at else None,
            "retry_count": self.retry_count,
            "error_code": self.error_code,
            "error_message": self.error_message,
            "payload_preview": self.payload_preview if mask_payload else None,
        }


class IntgMappingRule(db.Model):
    __tablename__ = "intg_mapping_rules"

    id = db.Column(db.String(36), primary_key=True, default=_uuid)
    connector_id = db.Column(db.String(36), nullable=False, index=True)
    organization_id = db.Column(db.String(36), nullable=False)
    external_field = db.Column(db.String(100), nullable=False)
    canonical_field = db.Column(db.String(100), nullable=False)
    transformation_type = db.Column(db.String(30), default="DIRECT")
    default_value = db.Column(db.String(255))
    required = db.Column(db.Boolean, default=False)
    value_mapping_json = db.Column(db.Text)
    date_format = db.Column(db.String(50))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "connector_id": self.connector_id,
            "external_field": self.external_field,
            "canonical_field": self.canonical_field,
            "transformation_type": self.transformation_type,
            "default_value": self.default_value,
            "required": self.required,
            "value_mapping": json.loads(self.value_mapping_json or "{}"),
            "date_format": self.date_format,
            "is_active": self.is_active,
        }


class IntgExternalMapping(db.Model):
    __tablename__ = "intg_external_mappings"
    __table_args__ = (
        db.UniqueConstraint("connector_id", "mapping_kind", "external_code", name="uq_intg_ext_map"),
    )

    id = db.Column(db.String(36), primary_key=True, default=_uuid)
    connector_id = db.Column(db.String(36), nullable=False)
    organization_id = db.Column(db.String(36), nullable=False)
    mapping_kind = db.Column(db.String(30), nullable=False)
    external_code = db.Column(db.String(100), nullable=False)
    internal_code = db.Column(db.String(100))
    status = db.Column(db.String(20), default="pending")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "connector_id": self.connector_id,
            "mapping_kind": self.mapping_kind,
            "external_code": self.external_code,
            "internal_code": self.internal_code,
            "status": self.status,
        }


class IntgWebhookSubscription(db.Model):
    __tablename__ = "intg_webhook_subscriptions"

    id = db.Column(db.String(36), primary_key=True, default=_uuid)
    organization_id = db.Column(db.String(36), nullable=False, index=True)
    connector_id = db.Column(db.String(36))
    event_type = db.Column(db.String(80), nullable=False)
    endpoint_url = db.Column(db.String(500), nullable=False)
    secret_reference = db.Column(db.String(255))
    status = db.Column(db.String(20), default="ACTIVE")
    retry_policy = db.Column(db.String(30), default="EXPONENTIAL_BACKOFF")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "organization_id": self.organization_id,
            "connector_id": self.connector_id,
            "event_type": self.event_type,
            "endpoint_url": self.endpoint_url,
            "status": self.status,
            "retry_policy": self.retry_policy,
        }


class IntgDeliveryAttempt(db.Model):
    __tablename__ = "intg_delivery_attempts"

    id = db.Column(db.String(36), primary_key=True, default=_uuid)
    subscription_id = db.Column(db.String(36), nullable=False, index=True)
    organization_id = db.Column(db.String(36), nullable=False)
    delivery_id = db.Column(db.String(80), unique=True, nullable=False)
    event_type = db.Column(db.String(80), nullable=False)
    payload_hash = db.Column(db.String(64))
    status = db.Column(db.String(20), nullable=False)
    attempt_number = db.Column(db.Integer, default=1)
    next_retry_at = db.Column(db.DateTime)
    last_error = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "subscription_id": self.subscription_id,
            "delivery_id": self.delivery_id,
            "event_type": self.event_type,
            "status": self.status,
            "attempt_number": self.attempt_number,
            "next_retry_at": self.next_retry_at.isoformat() if self.next_retry_at else None,
            "last_error": self.last_error,
        }


class IntgApiCredential(db.Model):
    __tablename__ = "intg_api_credentials"

    id = db.Column(db.String(36), primary_key=True, default=_uuid)
    organization_id = db.Column(db.String(36), nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    credential_type = db.Column(db.String(30), nullable=False)
    key_hash = db.Column(db.String(128), nullable=False)
    secret_reference = db.Column(db.String(255))
    scopes_json = db.Column(db.Text, default="[]")
    ip_allowlist_json = db.Column(db.Text)
    expires_at = db.Column(db.DateTime)
    revoked_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "organization_id": self.organization_id,
            "name": self.name,
            "credential_type": self.credential_type,
            "scopes": json.loads(self.scopes_json or "[]"),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "revoked_at": self.revoked_at.isoformat() if self.revoked_at else None,
        }


class IntgDeadLetter(db.Model):
    __tablename__ = "intg_dead_letters"

    id = db.Column(db.String(36), primary_key=True, default=_uuid)
    message_id = db.Column(db.String(36), nullable=False)
    organization_id = db.Column(db.String(36), nullable=False)
    connector_id = db.Column(db.String(36), nullable=False)
    retry_count = db.Column(db.Integer, default=0)
    maximum_retries = db.Column(db.Integer, default=5)
    last_error = db.Column(db.Text)
    retry_strategy = db.Column(db.String(30), default="EXPONENTIAL_BACKOFF")
    next_retry_at = db.Column(db.DateTime)
    status = db.Column(db.String(20), default="DEAD_LETTER")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "message_id": self.message_id,
            "connector_id": self.connector_id,
            "retry_count": self.retry_count,
            "status": self.status,
            "last_error": self.last_error,
        }


class IntgAuditEvent(db.Model):
    __tablename__ = "intg_audit_events"

    id = db.Column(db.String(36), primary_key=True, default=_uuid)
    action = db.Column(db.String(80), nullable=False, index=True)
    actor = db.Column(db.String(255))
    organization_id = db.Column(db.String(36), index=True)
    connector_id = db.Column(db.String(36))
    message_id = db.Column(db.String(36))
    correlation_id = db.Column(db.String(255))
    outcome = db.Column(db.String(20))
    detail_json = db.Column(db.Text, default="{}")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "action": self.action,
            "actor": self.actor,
            "organization_id": self.organization_id,
            "connector_id": self.connector_id,
            "message_id": self.message_id,
            "correlation_id": self.correlation_id,
            "outcome": self.outcome,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
