import json
import uuid

from app.extensions.db import db
from app.models.observability_platform import ObsAlert
from app.observability.health_service import HealthPlatformService
from app.observability.metrics import platform_metrics
from app.observability.metrics_service import MetricsPlatformService


ALERT_RULES = [
    {"code": "HIGH_API_LATENCY", "severity": "HIGH", "description": "High API latency"},
    {"code": "DATABASE_DOWN", "severity": "CRITICAL", "description": "Database unavailable"},
    {"code": "REDIS_UNAVAILABLE", "severity": "HIGH", "description": "Redis unavailable"},
    {"code": "SMTP_UNAVAILABLE", "severity": "MEDIUM", "description": "SMTP unavailable"},
    {"code": "WEBHOOK_FAILURES", "severity": "HIGH", "description": "Webhook failures"},
    {"code": "QUEUE_BACKLOG", "severity": "HIGH", "description": "Queue backlog"},
    {"code": "AUTH_FAILURES", "severity": "HIGH", "description": "Repeated authentication failures"},
    {"code": "CRITICAL_LAB_EVENT", "severity": "CRITICAL", "description": "Critical laboratory event"},
]


class AlertEngine:
    @staticmethod
    def evaluate_rules():
        health = HealthPlatformService.evaluate()
        generated = []
        for component in health["components"]:
            if component["component"] == "database" and component["status"] == "DOWN":
                generated.append(AlertEngine._create("DATABASE_DOWN", "Database is unavailable"))
            if component["component"] == "redis" and component["status"] == "DOWN":
                generated.append(AlertEngine._create("REDIS_UNAVAILABLE", "Redis is unavailable"))
            if component["component"] == "smtp" and component["status"] == "DOWN":
                generated.append(AlertEngine._create("SMTP_UNAVAILABLE", "SMTP is unavailable"))
            if component["component"] == "queue":
                depth = component.get("detail", {}).get("depth", 0)
                if depth > 100:
                    generated.append(AlertEngine._create("QUEUE_BACKLOG", f"Queue backlog at {depth}"))

        snapshot = platform_metrics.snapshot()
        auth_failures = snapshot["counters"].get("authentication_failures_total", 0)
        if auth_failures >= 5:
            generated.append(AlertEngine._create("AUTH_FAILURES", f"Authentication failures: {auth_failures}"))

        api_hist = snapshot["histograms"].get("api_latency_ms", {})
        if api_hist.get("avg", 0) > 1000:
            generated.append(AlertEngine._create("HIGH_API_LATENCY", f"Average API latency {api_hist['avg']}ms"))

        critical_total = snapshot["counters"].get("critical_results_total", 0)
        if critical_total > 0:
            generated.append(AlertEngine._create("CRITICAL_LAB_EVENT", f"Critical results detected: {critical_total}"))

        integration_failures = snapshot["counters"].get("integration_failures_total", 0)
        if integration_failures > 0:
            generated.append(AlertEngine._create("WEBHOOK_FAILURES", f"Integration failures: {integration_failures}"))

        return {"count": len(generated), "alerts": generated, "rules": ALERT_RULES}

    @staticmethod
    def _create(rule_code, message):
        row = ObsAlert(
            alert_code=f"OBS-ALT-{uuid.uuid4().hex[:8].upper()}",
            rule_code=rule_code,
            severity=next((rule["severity"] for rule in ALERT_RULES if rule["code"] == rule_code), "MEDIUM"),
            message=message,
            status="OPEN",
        )
        db.session.add(row)
        db.session.commit()
        return row.to_dict()

    @staticmethod
    def list_alerts(limit=100):
        rows = ObsAlert.query.order_by(ObsAlert.created_at.desc()).limit(limit).all()
        return {"count": len(rows), "alerts": [row.to_dict() for row in rows], "rules": ALERT_RULES}

    @staticmethod
    def test_alert(data=None):
        data = data or {}
        rule_code = data.get("rule_code") or "HIGH_API_LATENCY"
        message = data.get("message") or f"Test alert for {rule_code}"
        alert = AlertEngine._create(rule_code, message)
        MetricsPlatformService.record_integration_failure() if rule_code == "WEBHOOK_FAILURES" else None
        return {"message": "Test alert generated", "alert": alert}
