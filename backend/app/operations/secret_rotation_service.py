import hashlib
import json
import uuid
from datetime import datetime, timedelta

from flask import current_app

from app.extensions.db import db
from app.models.operations_platform import SecretRotationEvent, SecretRotationPlan
from app.operations.backup_service import OperationsPlatformError


REQUIRED_SECRETS = ("SECRET_KEY", "JWT_SECRET_KEY", "SMTP_PASSWORD", "DATABASE_URL")


class SecretRotationService:
    @staticmethod
    def _fingerprint(value):
        return hashlib.sha256(str(value or "missing").encode()).hexdigest()[:32]

    @staticmethod
    def ensure_defaults():
        if SecretRotationPlan.query.first():
            return {"seeded": False}
        app = current_app._get_current_object()
        for name in REQUIRED_SECRETS:
            raw = app.config.get(name) or app.config.get(name.replace("DATABASE_URL", "SQLALCHEMY_DATABASE_URI"))
            db.session.add(
                SecretRotationPlan(
                    secret_name=name,
                    fingerprint=SecretRotationService._fingerprint(raw),
                    rotation_interval_days=90,
                    last_rotated_at=datetime.utcnow() - timedelta(days=30),
                    expires_at=datetime.utcnow() + timedelta(days=60),
                    status="ACTIVE",
                )
            )
        db.session.commit()
        return {"seeded": True}

    @staticmethod
    def list_secrets():
        rows = SecretRotationPlan.query.order_by(SecretRotationPlan.secret_name.asc()).all()
        return {"count": len(rows), "secrets": [row.to_dict() for row in rows]}

    @staticmethod
    def validate_secrets():
        app = current_app._get_current_object()
        warnings = []
        validated = []
        for name in REQUIRED_SECRETS:
            config_key = "SQLALCHEMY_DATABASE_URI" if name == "DATABASE_URL" else name
            value = app.config.get(config_key) or app.config.get(name)
            fingerprint = SecretRotationService._fingerprint(value)
            plan = SecretRotationPlan.query.filter_by(secret_name=name).first()
            if value in (None, "", "change-me", "dev-secret"):
                warnings.append({"secret_name": name, "issue": "missing_or_default"})
            if plan and plan.expires_at and plan.expires_at < datetime.utcnow():
                warnings.append({"secret_name": name, "issue": "expired"})
            validated.append({"secret_name": name, "fingerprint": fingerprint, "configured": bool(value)})
        return {"validated": validated, "warnings": warnings, "required": list(REQUIRED_SECRETS)}

    @staticmethod
    def create_rotation_plan(data):
        name = data.get("secret_name")
        if not name:
            raise OperationsPlatformError("secret_name is required")
        plan = SecretRotationPlan.query.filter_by(secret_name=name).first()
        if plan is None:
            plan = SecretRotationPlan(
                secret_name=name,
                fingerprint=SecretRotationService._fingerprint(data.get("fingerprint")),
                rotation_interval_days=int(data.get("rotation_interval_days") or 90),
            )
            db.session.add(plan)
        else:
            plan.rotation_interval_days = int(data.get("rotation_interval_days") or plan.rotation_interval_days)
            if data.get("fingerprint"):
                plan.fingerprint = data["fingerprint"]
        plan.expires_at = datetime.utcnow() + timedelta(days=plan.rotation_interval_days)
        plan.status = "ACTIVE"
        db.session.commit()
        return plan.to_dict()

    @staticmethod
    def mark_rotated(plan_id, data=None):
        data = data or {}
        plan = SecretRotationPlan.query.filter_by(id=plan_id).first()
        if plan is None:
            raise OperationsPlatformError("Secret plan not found", 404)
        app = current_app._get_current_object()
        config_key = "SQLALCHEMY_DATABASE_URI" if plan.secret_name == "DATABASE_URL" else plan.secret_name
        fingerprint = SecretRotationService._fingerprint(app.config.get(config_key))
        plan.fingerprint = data.get("fingerprint") or fingerprint
        plan.last_rotated_at = datetime.utcnow()
        plan.expires_at = datetime.utcnow() + timedelta(days=plan.rotation_interval_days)
        event = SecretRotationEvent(
            plan_id=plan.id,
            event_code=f"SRE-{uuid.uuid4().hex[:8].upper()}",
            action="ROTATED",
            fingerprint=plan.fingerprint,
            detail_json=json.dumps({"note": "Metadata only; secret value not stored"}),
        )
        db.session.add(event)
        db.session.commit()
        return {"plan": plan.to_dict(), "event": event.to_dict()}
