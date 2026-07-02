"""Observability and monitoring stack validation for staging sprint 2."""

from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
MONITORING = REPO / "deployment" / "monitoring"

PROMETHEUS_FILE = MONITORING / "prometheus.yml"
ALERTS_FILE = MONITORING / "alerts" / "dxcon-alerts.yml"
GRAFANA_DATASOURCES = MONITORING / "grafana" / "provisioning" / "datasources" / "datasources.yml"
GRAFANA_DASHBOARDS = MONITORING / "grafana" / "provisioning" / "dashboards" / "dashboards.yml"
GRAFANA_OVERVIEW = MONITORING / "grafana" / "dashboards" / "dxcon-overview.json"

REQUIRED_PROMETHEUS_METRICS = (
    "http_requests_total",
    "http_errors_total",
    "api_latency_ms",
    "db_health",
    "redis_health",
    "queue_depth",
    "notification_delivery_success_total",
    "notification_delivery_failures_total",
    "webhook_delivery_failures_total",
    "background_job_pending",
    "readiness_ok",
)

REQUIRED_ALERTS = (
    "ApiErrorRateHigh",
    "DatabaseUnavailable",
    "RedisUnavailable",
    "QueueBacklogHigh",
    "WebhookDeliveryFailures",
    "NotificationDeliveryFailures",
    "ReadinessFailed",
)

REQUIRED_DASHBOARD_PANELS = (
    "DxCon API Up",
    "API Request Rate",
    "API Error Rate",
    "Queue Depth",
    "Database Health",
    "Redis Health",
)


def find_duplicate_routes(app):
    seen = defaultdict(list)
    for rule in app.url_map.iter_rules():
        methods = sorted(m for m in rule.methods if m not in {"HEAD", "OPTIONS"})
        key = (str(rule.rule), tuple(methods))
        seen[key].append(rule.endpoint)
    return {str(key): endpoints for key, endpoints in seen.items() if len(endpoints) > 1}


def verify_prometheus_config() -> dict:
    if not PROMETHEUS_FILE.exists():
        return {"ok": False, "error": "missing prometheus.yml"}
    text = PROMETHEUS_FILE.read_text(encoding="utf-8")
    checks = {
        "scrape_configs": "scrape_configs:" in text,
        "dxcon_api_job": 'job_name: dxcon-api' in text,
        "prometheus_metrics_path": "/metrics/prometheus" in text,
        "alertmanager_target": "alertmanager:9093" in text,
        "health_job": "dxcon-health" in text,
        "rule_files": "rule_files:" in text,
    }
    return {"ok": all(checks.values()), "checks": checks}


def verify_alert_rules() -> dict:
    if not ALERTS_FILE.exists():
        return {"ok": False, "error": "missing dxcon-alerts.yml"}
    text = ALERTS_FILE.read_text(encoding="utf-8")
    present = [name for name in REQUIRED_ALERTS if f"alert: {name}" in text]
    missing = [name for name in REQUIRED_ALERTS if name not in present]
    return {
        "ok": not missing,
        "present": present,
        "missing": missing,
        "count": len(present),
    }


def verify_grafana_provisioning() -> dict:
    missing = [
        str(path.relative_to(REPO))
        for path in (GRAFANA_DATASOURCES, GRAFANA_DASHBOARDS, GRAFANA_OVERVIEW)
        if not path.exists()
    ]
    datasource_text = GRAFANA_DATASOURCES.read_text(encoding="utf-8") if GRAFANA_DATASOURCES.exists() else ""
    dashboard_text = GRAFANA_DASHBOARDS.read_text(encoding="utf-8") if GRAFANA_DASHBOARDS.exists() else ""
    overview = {}
    if GRAFANA_OVERVIEW.exists():
        overview = json.loads(GRAFANA_OVERVIEW.read_text(encoding="utf-8"))
    panel_titles = [panel.get("title", "") for panel in overview.get("panels", [])]
    missing_panels = [title for title in REQUIRED_DASHBOARD_PANELS if title not in panel_titles]
    checks = {
        "prometheus_datasource": "Prometheus" in datasource_text,
        "loki_datasource": "Loki" in datasource_text,
        "dashboard_provider": "providers:" in dashboard_text,
        "overview_dashboard": GRAFANA_OVERVIEW.exists(),
        "required_panels": not missing_panels,
    }
    return {
        "ok": not missing and all(checks.values()),
        "missing": missing,
        "missing_panels": missing_panels,
        "checks": checks,
        "panel_count": len(panel_titles),
    }


def verify_log_readiness() -> dict:
    import os

    os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
    from app import create_app
    from app.core.logging_config import JsonLogFormatter, redact_mapping, sanitize_path
    from app.observability.logging_service import StructuredLoggingService

    app = create_app()
    app.config.update({"TESTING": True, "LOG_FORMAT": "json", "LOG_LEVEL": "INFO"})
    from app.extensions.db import db

    with app.app_context():
        db.create_all()
        client = app.test_client()
        response = client.get(
            "/live",
            headers={
                "X-Request-ID": "monitoring-req-001",
                "X-Correlation-ID": "monitoring-corr-001",
            },
        )
        request_id = response.headers.get("X-Request-ID")
        correlation_id = response.headers.get("X-Correlation-ID")

    redacted = redact_mapping({"password": "secret123", "email": "user@example.com"})
    sanitized = sanitize_path("/api/v1/auth/login?token=abc123")
    structured = StructuredLoggingService.sanitize({"api_key": "abc", "status": "OK"})

    formatter = JsonLogFormatter()
    import logging

    record = logging.LogRecord(
        name="dxcon.test",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="test message",
        args=(),
        exc_info=None,
    )
    record.request_id = "rid-1"
    record.correlation_id = "cid-1"
    record_text = formatter.format(record)
    parsed = json.loads(record_text)

    checks = {
        "json_log_format": app.config.get("LOG_FORMAT") == "json",
        "request_id_header": request_id == "monitoring-req-001",
        "correlation_id_header": correlation_id == "monitoring-corr-001",
        "json_formatter": "timestamp" in parsed and "level" in parsed,
        "password_redacted": redacted.get("password") == "[REDACTED]",
        "query_token_redacted": "token=[REDACTED]" in sanitized,
        "structured_redaction": structured.get("api_key") == "[REDACTED]",
    }
    return {"ok": all(checks.values()), "checks": checks}


def verify_prometheus_metrics_endpoint() -> dict:
    import os

    os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
    from app import create_app
    from app.extensions.db import db
    from app.observability.metrics_service import MetricsPlatformService

    app = create_app()
    app.config["TESTING"] = True
    with app.app_context():
        db.create_all()
        client = app.test_client()
        client.get("/live")
        client.get("/api/v1/system/health")
        MetricsPlatformService.refresh_runtime_metrics(app)
        response = client.get("/metrics/prometheus")
        body = response.get_data(as_text=True)

    present = [name for name in REQUIRED_PROMETHEUS_METRICS if name in body]
    missing = [name for name in REQUIRED_PROMETHEUS_METRICS if name not in body]
    return {
        "ok": response.status_code == 200 and not missing,
        "status_code": response.status_code,
        "present": present,
        "missing": missing,
        "sample_lines": [line for line in body.splitlines() if line and not line.startswith("#")][:8],
    }


def verify_route_inventory() -> dict:
    import os

    os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
    from app import create_app

    app = create_app()
    duplicates = find_duplicate_routes(app)
    return {"ok": not duplicates, "count": len(duplicates)}


def run_monitoring_stack_verification() -> dict:
    checks = {
        "prometheus": verify_prometheus_config(),
        "alert_rules": verify_alert_rules(),
        "grafana": verify_grafana_provisioning(),
        "log_readiness": verify_log_readiness(),
        "prometheus_metrics": verify_prometheus_metrics_endpoint(),
        "route_inventory": verify_route_inventory(),
    }
    passed = sum(1 for item in checks.values() if item.get("ok"))
    return {
        "ok": passed == len(checks),
        "passed": passed,
        "total": len(checks),
        "checks": checks,
    }


def run_uat_monitoring_smoke() -> dict:
    import os

    os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
    from app import create_app
    from app.extensions.db import db

    verification = run_monitoring_stack_verification()
    app = create_app()
    app.config.update({"TESTING": True, "LOG_FORMAT": "json"})
    client = app.test_client()
    steps = {}

    with app.app_context():
        db.create_all()
        steps["stack_verification"] = verification["ok"]
        steps["live_probe"] = client.get("/live").status_code == 200
        steps["ready_probe"] = client.get("/ready").status_code == 200
        steps["health_probe"] = client.get("/api/v1/system/health").status_code == 200
        steps["metrics_probe"] = client.get("/metrics/prometheus").status_code == 200
        steps["system_metrics_probe"] = client.get("/api/v1/system/metrics").status_code == 200
        steps["request_id_header"] = verification["checks"]["log_readiness"]["checks"]["request_id_header"]
        steps["alert_rules_present"] = verification["checks"]["alert_rules"]["ok"]
        steps["grafana_dashboard"] = verification["checks"]["grafana"]["ok"]

    passed = sum(1 for ok in steps.values() if ok)
    return {
        "ok": passed == len(steps) and verification["ok"],
        "passed": passed,
        "total": len(steps),
        "steps": steps,
        "verification": verification,
    }
