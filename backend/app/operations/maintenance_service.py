import uuid
from datetime import datetime, timedelta

from app.extensions.db import db
from app.models.operations_platform import MaintenanceWindow
from app.operations.backup_service import OperationsPlatformError


class MaintenanceService:
    _active_window_id = None

    @classmethod
    def status(cls):
        active = MaintenanceWindow.query.filter_by(active=True).order_by(MaintenanceWindow.created_at.desc()).first()
        scheduled = MaintenanceWindow.query.filter_by(status="SCHEDULED").order_by(MaintenanceWindow.starts_at.asc()).all()
        return {
            "active": active.to_dict() if active else None,
            "scheduled": [row.to_dict() for row in scheduled],
            "banner": cls.banner_payload(active),
        }

    @classmethod
    def banner_payload(cls, window=None):
        if window is None:
            window = MaintenanceWindow.query.filter_by(active=True).first()
        if window is None:
            return {"enabled": False}
        return {
            "enabled": True,
            "title": window.title,
            "message": window.message,
            "starts_at": window.starts_at.isoformat() if window.starts_at else None,
            "ends_at": window.ends_at.isoformat() if window.ends_at else None,
        }

    @classmethod
    def is_active(cls):
        return MaintenanceWindow.query.filter_by(active=True).count() > 0

    @classmethod
    def enable(cls, data=None):
        data = data or {}
        MaintenanceWindow.query.filter_by(active=True).update({"active": False, "status": "COMPLETED"})
        window = MaintenanceWindow(
            window_code=data.get("window_code") or f"MW-{uuid.uuid4().hex[:8].upper()}",
            title=data.get("title") or "Maintenance Mode",
            message=data.get("message") or "System maintenance in progress",
            status="ACTIVE",
            starts_at=datetime.utcnow(),
            ends_at=data.get("ends_at"),
            active=True,
        )
        db.session.add(window)
        db.session.commit()
        cls._active_window_id = window.id
        return window.to_dict()

    @classmethod
    def disable(cls):
        MaintenanceWindow.query.filter_by(active=True).update({"active": False, "status": "COMPLETED"})
        db.session.commit()
        cls._active_window_id = None
        return {"active": False, "message": "Maintenance mode disabled"}

    @classmethod
    def schedule(cls, data):
        if not data.get("title") or not data.get("starts_at"):
            raise OperationsPlatformError("title and starts_at are required")
        starts_at = datetime.fromisoformat(data["starts_at"].replace("Z", ""))
        ends_at = datetime.fromisoformat(data["ends_at"].replace("Z", "")) if data.get("ends_at") else starts_at + timedelta(hours=2)
        window = MaintenanceWindow(
            window_code=data.get("window_code") or f"MW-{uuid.uuid4().hex[:8].upper()}",
            title=data["title"],
            message=data.get("message") or "Scheduled maintenance",
            status="SCHEDULED",
            starts_at=starts_at,
            ends_at=ends_at,
            active=False,
        )
        db.session.add(window)
        db.session.commit()
        return window.to_dict()

    @classmethod
    def init_app(cls, app):
        exempt_prefixes = (
            "/health",
            "/ready",
            "/live",
            "/api/v1/system/health",
            "/api/v1/system/ready",
            "/api/v1/system/live",
        )

        @app.before_request
        def _maintenance_guard():
            from flask import jsonify, request

            if not cls.is_active():
                return None
            path = request.path or ""
            if request.method in {"GET", "HEAD", "OPTIONS"}:
                return None
            if any(path.startswith(prefix) for prefix in exempt_prefixes):
                return None
            if path.startswith("/api/v1/operations/maintenance"):
                return None
            banner = cls.banner_payload()
            return jsonify({"error": "MAINTENANCE_MODE", "banner": banner}), 503
