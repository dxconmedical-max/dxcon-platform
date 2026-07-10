"""Mobile MVP models — Epic 7."""

from __future__ import annotations

import uuid
from datetime import datetime

from app.extensions.db import db


class MobileDevice(db.Model):
    __tablename__ = "mobile_devices"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    device_reference = db.Column(db.String(80), unique=True, nullable=False)
    user_id = db.Column(db.String(36), nullable=False, index=True)
    organization_id = db.Column(db.String(36), index=True)
    platform = db.Column(db.String(20), nullable=False)
    app_version = db.Column(db.String(30))
    notification_token_hash = db.Column(db.String(64))
    workspace = db.Column(db.String(30))
    status = db.Column(db.String(20), default="ACTIVE")
    last_seen_at = db.Column(db.DateTime)
    revoked_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "device_reference": self.device_reference,
            "platform": self.platform,
            "app_version": self.app_version,
            "workspace": self.workspace,
            "status": self.status,
            "last_seen_at": self.last_seen_at.isoformat() if self.last_seen_at else None,
        }


class MobileAuditEvent(db.Model):
    __tablename__ = "mobile_audit_events"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = db.Column(db.String(36), index=True)
    user_id = db.Column(db.String(36), index=True)
    workspace = db.Column(db.String(30))
    event_type = db.Column(db.String(80), nullable=False)
    resource_type = db.Column(db.String(50))
    resource_id = db.Column(db.String(36))
    outcome = db.Column(db.String(30), default="SUCCESS")
    correlation_id = db.Column(db.String(80))
    metadata_json = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "event_type": self.event_type,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "outcome": self.outcome,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
