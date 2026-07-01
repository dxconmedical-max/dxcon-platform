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
        db.session.execute(text("SELECT 1"))
        return {"status": "OK", "engine": (app.config.get("SQLALCHEMY_DATABASE_URI") or "").split(":", 1)[0]}

    @staticmethod
    def check_redis(app):
        if not app.config.get("REDIS_URL"):
            return {"status": "DEGRADED", "mode": "not_configured"}
        return {"status": "OK", "mode": "configured"}

    @staticmethod
    def check_storage(app):
        import os
        import tempfile

        path = tempfile.gettempdir()
        return {"status": "OK" if os.access(path, os.W_OK) else "DOWN", "path": path}

    @staticmethod
    def check_smtp(app):
        if app.config.get("SMTP_HOST"):
            return {"status": "OK", "host": app.config.get("SMTP_HOST")}
        return {"status": "DEGRADED", "mode": "demo"}

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
        from app.core.startup_checks import run_startup_checks
        from app.observability.health_service import HealthPlatformService

        cached = app.extensions.get("dxcon_startup", {}).get("checks")
        startup = cached if cached else run_startup_checks(app)
        if isinstance(startup, dict):
            checks = startup.get("checks", [])
            failed = [item for item in checks if item.get("status") == "fail"]
            app_status = startup.get("status", "OK")
            if failed and app_status == "OK":
                app_status = "DEGRADED"
        else:
            checks = startup if isinstance(startup, list) else []
            app_status = "OK"

        components = [{"component": "application", "status": app_status, "checks": len(checks)}]
        overall = app_status
        for name in (
            "database",
            "redis",
            "storage",
            "smtp",
            "queue",
            "scheduler",
            "event_bus",
            "webhook_engine",
            "plugin_framework",
            "integration_platform",
        ):
            fn = getattr(HealthPlatformService, f"check_{name}", None)
            if fn is None:
                continue
            try:
                result = fn()
                status = result.get("status", "OK")
            except Exception as exc:
                status = "DOWN"
                result = {"error": str(exc)}
            components.append({"component": name, "status": status})
            if status == "DOWN":
                overall = "DOWN"
            elif status != "OK" and overall == "OK":
                overall = "DEGRADED"
        return {"status": overall, "components": components}

    @staticmethod
    def check_operations_platform(app):
        from app.operations.scheduler_service import SchedulerService

        SchedulerService.ensure_defaults()
        return {"status": "OK", "jobs": SchedulerService.list_jobs()["count"]}

    @staticmethod
    def validate_runtime_config(app=None):
        return RuntimeConfig.validate(app)
