from datetime import datetime
import uuid

from app.extensions.db import db


class IntegrationConnector(db.Model):
    __tablename__ = "integration_connectors"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    connector_code = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(255), nullable=False)
    adapter_type = db.Column(db.String(50), nullable=False, index=True)
    config_json = db.Column(db.Text, default="{}")
    status = db.Column(db.String(50), default="ACTIVE")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "connector_code": self.connector_code,
            "name": self.name,
            "adapter_type": self.adapter_type,
            "config_json": self.config_json,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class IntegrationPlatformAuditLog(db.Model):
    __tablename__ = "integration_platform_audit_logs"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    action = db.Column(db.String(100), nullable=False, index=True)
    resource_type = db.Column(db.String(100), nullable=False)
    resource_id = db.Column(db.String(100))
    actor = db.Column(db.String(255), default="SYSTEM")
    detail_json = db.Column(db.Text, default="{}")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "action": self.action,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "actor": self.actor,
            "detail_json": self.detail_json,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class PartnerSandboxToken(db.Model):
    __tablename__ = "partner_sandbox_tokens"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    partner_id = db.Column(db.String(100), nullable=False, index=True)
    token_hash = db.Column(db.String(128), unique=True, nullable=False)
    scopes_json = db.Column(db.Text, default="[]")
    expires_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "partner_id": self.partner_id,
            "scopes_json": self.scopes_json,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
