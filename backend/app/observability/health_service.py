from flask import current_app
from sqlalchemy import text

from app.core.database_startup import verify_database_connection, verify_migrations
from app.core.metrics import metrics
from app.core.startup_checks import run_startup_checks
from app.extensions.db import db
from app.models.observability_platform import ObsHealthEvent


class HealthPlatformService:
    COMPONENTS = (
        "application",
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
    )

    @staticmethod
    def _component_status(name, checker):
        try:
            result = checker()
            status = result.get("status", "OK")
            detail = result
        except Exception as exc:
            status = "DOWN"
            detail = {"status": "DOWN", "error": str(exc)}
        return {"component": name, "status": status, "detail": detail}

    @staticmethod
    def check_application():
        app = current_app._get_current_object()
        cached = app.extensions.get("dxcon_startup", {}).get("checks")
        startup = cached if cached else run_startup_checks(app)
        if isinstance(startup, dict):
            checks = startup.get("checks", [])
            failed = [item for item in checks if item.get("status") == "fail"]
            status = startup.get("status", "OK")
            if failed and status == "OK":
                status = "DEGRADED"
            return {"status": status, "checks": checks}
        failed = [item for item in startup if item.get("status") in {"fail", "DOWN"}]
        return {"status": "OK" if not failed else "DEGRADED", "checks": startup}

    @staticmethod
    def check_database():
        app = current_app._get_current_object()
        verify_database_connection(app, retries=1, delay_seconds=0)
        db.session.execute(text("SELECT 1"))
        return {"status": "OK", "engine": app.config.get("SQLALCHEMY_DATABASE_URI", "").split(":", 1)[0]}

    @staticmethod
    def check_redis():
        app = current_app._get_current_object()
        if not app.config.get("REDIS_URL"):
            return {"status": "DEGRADED", "mode": "not_configured"}
        return {"status": "OK", "mode": "configured"}

    @staticmethod
    def check_storage():
        import os
        import tempfile

        path = tempfile.gettempdir()
        writable = os.access(path, os.W_OK)
        return {"status": "OK" if writable else "DOWN", "path": path}

    @staticmethod
    def check_smtp():
        app = current_app._get_current_object()
        if app.config.get("SMTP_HOST"):
            return {"status": "OK", "host": app.config.get("SMTP_HOST")}
        return {"status": "DEGRADED", "mode": "demo"}

    @staticmethod
    def check_queue():
        try:
            from app.models.integration_platform import IntegrationJob

            depth = IntegrationJob.query.filter_by(status="QUEUED").count()
            return {"status": "OK", "depth": depth}
        except Exception:
            return {"status": "OK", "depth": 0}

    @staticmethod
    def check_scheduler():
        return {"status": "OK", "mode": "embedded"}

    @staticmethod
    def check_event_bus():
        from app.events.event_registry import EventRegistry

        return {"status": "OK", "handlers": len(EventRegistry._handlers)}

    @staticmethod
    def check_webhook_engine():
        try:
            from app.models.integration_platform import WebhookEndpoint

            count = WebhookEndpoint.query.count()
            return {"status": "OK", "endpoints": count}
        except Exception:
            return {"status": "OK", "endpoints": 0}

    @staticmethod
    def check_plugin_framework():
        try:
            from app.models.integration_platform import IntegrationPluginState

            count = IntegrationPluginState.query.count()
            return {"status": "OK", "plugins": count}
        except Exception:
            return {"status": "OK", "plugins": 0}

    @staticmethod
    def check_integration_platform():
        return HealthPlatformService.check_queue()

    @staticmethod
    def evaluate():
        checks = {
            "application": HealthPlatformService.check_application,
            "database": HealthPlatformService.check_database,
            "redis": HealthPlatformService.check_redis,
            "storage": HealthPlatformService.check_storage,
            "smtp": HealthPlatformService.check_smtp,
            "queue": HealthPlatformService.check_queue,
            "scheduler": HealthPlatformService.check_scheduler,
            "event_bus": HealthPlatformService.check_event_bus,
            "webhook_engine": HealthPlatformService.check_webhook_engine,
            "plugin_framework": HealthPlatformService.check_plugin_framework,
            "integration_platform": HealthPlatformService.check_integration_platform,
        }
        components = []
        overall = "OK"
        for name, fn in checks.items():
            item = HealthPlatformService._component_status(name, fn)
            components.append(item)
            if item["status"] == "DOWN":
                overall = "DOWN"
            elif item["status"] != "OK" and overall == "OK":
                overall = "DEGRADED"
        metrics.set_health_status(overall)
        return {"status": overall, "components": components}

    @staticmethod
    def live():
        return {"alive": True, "status": "OK"}

    @staticmethod
    def ready():
        app = current_app._get_current_object()
        try:
            verify_database_connection(app, retries=1, delay_seconds=0)
            migration = verify_migrations(app)
            ready = bool(migration.get("ready", True))
            return {"ready": ready, "migration": migration}, (200 if ready else 503)
        except Exception as exc:
            return {"ready": False, "error": str(exc)}, 503

    @staticmethod
    def health():
        payload = HealthPlatformService.evaluate()
        return payload, (200 if payload["status"] != "DOWN" else 503)

    @staticmethod
    def record_event(component, status, detail=None):
        import json

        row = ObsHealthEvent(
            component=component,
            status=status,
            detail_json=json.dumps(detail or {}),
        )
        db.session.add(row)
        db.session.commit()
        return row.to_dict()
