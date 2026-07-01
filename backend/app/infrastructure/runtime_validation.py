from flask import current_app
from sqlalchemy import text

from app.extensions.db import db
from app.runtime.runtime_config import RuntimeConfig


class RuntimeValidationService:
    CHECKS = (
        "database",
        "redis",
        "storage",
        "smtp",
        "jwt",
        "secret_keys",
        "plugin_registry",
        "integration_platform",
        "notification_platform",
        "observability_platform",
        "operations_platform",
    )

    @staticmethod
    def validate_all(app=None):
        app = app or current_app._get_current_object()
        results = []
        for name in RuntimeValidationService.CHECKS:
            checker = getattr(RuntimeValidationService, f"check_{name}", None)
            if checker is None:
                results.append({"component": name, "status": "SKIPPED"})
                continue
            try:
                payload = checker(app)
                results.append({"component": name, **payload})
            except Exception as exc:
                results.append({"component": name, "status": "DOWN", "error": str(exc)})
        overall = "OK"
        for item in results:
            if item.get("status") == "DOWN":
                overall = "DOWN"
            elif item.get("status") in {"DEGRADED", "WARNING"} and overall == "OK":
                overall = "DEGRADED"
        return {"status": overall, "checks": results}

    @staticmethod
    def check_database(app):
        from app.infrastructure.production_readiness import database_dialect_report

        db.session.execute(text("SELECT 1"))
        report = database_dialect_report(app)
        status = "OK" if report["ok"] else "DOWN"
        if report.get("sqlite_blocked_in_env"):
            status = "DOWN"
        return {"status": status, "engine": report["dialect"], "report": report}

    @staticmethod
    def check_redis(app):
        from app.infrastructure.production_readiness import check_redis_health

        payload = check_redis_health(app)
        return {
            "status": payload.get("status", "DEGRADED"),
            "mode": payload.get("mode"),
            "required": payload.get("required", False),
        }

    @staticmethod
    def check_storage(app):
        import os
        import tempfile

        path = tempfile.gettempdir()
        return {"status": "OK" if os.access(path, os.W_OK) else "DOWN", "path": path}

    @staticmethod
    def check_smtp(app):
        from app.infrastructure.production_readiness import check_smtp_readiness

        payload = check_smtp_readiness(app)
        return {
            "status": payload.get("status", "DEGRADED"),
            "mode": payload.get("mode", "configured"),
            "blocker": payload.get("blocker", False),
        }

    @staticmethod
    def check_jwt(app):
        secret = app.config.get("JWT_SECRET_KEY") or app.config.get("SECRET_KEY")
        return {"status": "OK" if secret else "DOWN", "configured": bool(secret)}

    @staticmethod
    def check_secret_keys(app):
        issues = []
        if not app.config.get("SECRET_KEY"):
            issues.append("SECRET_KEY")
        if not app.config.get("JWT_SECRET_KEY"):
            issues.append("JWT_SECRET_KEY")
        return {"status": "OK" if not issues else "DOWN", "missing": issues}

    @staticmethod
    def check_plugin_registry(app):
        from app.events.event_registry import EventRegistry

        return {"status": "OK", "handlers": len(EventRegistry._handlers)}

    @staticmethod
    def check_integration_platform(app):
        from app.models.integration_platform import IntegrationPluginState

        return {"status": "OK", "plugins": IntegrationPluginState.query.count()}

    @staticmethod
    def check_notification_platform(app):
        from app.models.notification_center import NCNotificationProvider

        return {"status": "OK", "providers": NCNotificationProvider.query.count()}

    @staticmethod
    def check_observability_platform(app):
        from app.observability.health_service import HealthPlatformService

        return HealthPlatformService.evaluate()

    @staticmethod
    def check_operations_platform(app):
        from app.operations.scheduler_service import SchedulerService

        SchedulerService.ensure_defaults()
        return {"status": "OK", "jobs": SchedulerService.list_jobs()["count"]}

    @staticmethod
    def validate_runtime_config(app=None):
        return RuntimeConfig.validate(app)
