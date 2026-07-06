"""Sprint 010 — Executive platform models."""

from __future__ import annotations

from datetime import datetime
import uuid

from app.extensions.db import db


class LaunchChecklistItem(db.Model):
    __tablename__ = "launch_checklist_items"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    category = db.Column(db.String(50), nullable=False)
    item_key = db.Column(db.String(100), unique=True, nullable=False)
    label = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(30), default="pending")
    verified_at = db.Column(db.DateTime)
    verified_by = db.Column(db.String(255))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "category": self.category,
            "item_key": self.item_key,
            "label": self.label,
            "status": self.status,
            "verified_at": self.verified_at.isoformat() if self.verified_at else None,
            "verified_by": self.verified_by,
            "notes": self.notes,
        }


class PilotWizardSession(db.Model):
    __tablename__ = "pilot_wizard_sessions"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_name = db.Column(db.String(255))
    current_step = db.Column(db.String(50), default="organization")
    checklist_json = db.Column(db.Text)
    status = db.Column(db.String(30), default="in_progress")
    created_by = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "organization_name": self.organization_name,
            "current_step": self.current_step,
            "status": self.status,
            "created_by": self.created_by,
        }


class StorageConfig(db.Model):
    __tablename__ = "storage_config"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    provider = db.Column(db.String(30), default="local")
    bucket_name = db.Column(db.String(255))
    base_path = db.Column(db.String(500))
    is_active = db.Column(db.Boolean, default=True)
    config_json = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "provider": self.provider,
            "bucket_name": self.bucket_name,
            "base_path": self.base_path,
            "is_active": self.is_active,
        }
