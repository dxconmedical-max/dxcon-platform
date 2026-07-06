"""Sprint 009 — Portal models."""

from __future__ import annotations

from datetime import datetime
import uuid

from app.extensions.db import db

NOTIFICATION_CHANNELS = ("IN_APP", "EMAIL", "SMS", "ZALO", "PUSH", "WEBHOOK")
PORTAL_EVENTS = (
    "report_released",
    "invoice_created",
    "collection_reminder",
    "critical_result",
    "system_announcement",
)


class PortalNotification(db.Model):
    __tablename__ = "portal_notifications"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    recipient_type = db.Column(db.String(30), nullable=False, index=True)
    recipient_id = db.Column(db.String(50), nullable=False, index=True)
    event_type = db.Column(db.String(50), nullable=False)
    channel = db.Column(db.String(30), default="IN_APP")
    title = db.Column(db.String(255))
    body = db.Column(db.Text)
    status = db.Column(db.String(30), default="unread", index=True)
    payload_json = db.Column(db.Text)
    read_at = db.Column(db.DateTime)
    organization_id = db.Column(db.String(36))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "recipient_type": self.recipient_type,
            "recipient_id": self.recipient_id,
            "event_type": self.event_type,
            "channel": self.channel,
            "title": self.title,
            "body": self.body,
            "status": self.status,
            "read_at": self.read_at.isoformat() if self.read_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class PortalQrToken(db.Model):
    __tablename__ = "portal_qr_tokens"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = db.Column(db.String(50), nullable=False, index=True)
    verification_token = db.Column(db.String(128), unique=True, nullable=False)
    organization_id = db.Column(db.String(36))
    qr_payload = db.Column(db.String(255))
    expires_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "patient_id": self.patient_id,
            "verification_token": self.verification_token,
            "organization_id": self.organization_id,
            "qr_payload": self.qr_payload,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
        }


class PortalFavorite(db.Model):
    __tablename__ = "portal_favorites"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    owner_type = db.Column(db.String(20), nullable=False)
    owner_id = db.Column(db.String(50), nullable=False, index=True)
    favorite_type = db.Column(db.String(30), nullable=False)
    favorite_id = db.Column(db.String(50), nullable=False)
    label = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "owner_type": self.owner_type,
            "owner_id": self.owner_id,
            "favorite_type": self.favorite_type,
            "favorite_id": self.favorite_id,
            "label": self.label,
        }
