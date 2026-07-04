"""Monitoring Center business logic for Phase 5 Sprint 5.2."""

from __future__ import annotations

from typing import Any

from flask import current_app

from app.core.background_tasks import background_tasks
from app.core.database_startup import verify_database_connection, verify_migrations
from app.core.metrics import metrics as core_metrics
from app.infrastructure.production_health import health_payload
from app.infrastructure.production_readiness import check_redis_health
from app.models.operations_platform import ScheduledJob, ScheduledJobRun
from app.observability.alert_engine import ALERT_RULES, AlertEngine
from app.observability.health_service import HealthPlatformService
from app.observability.metrics import platform_metrics
from app.observability.metrics_service import MetricsPlatformService
from app.operations.queue_operations_service import QueueOperationsService
from app.services.kpi_engine_service import KPIEngineService
from app.services.reporting_service import _safe

MONITORING_ROLES = ("SUPER_ADMIN", "ADMIN")

FEATURES = (
    "Application Health",
    "Queue Health",
    "Database Health",
    "Redis Health",
    "API Latency",
    "Error Rate",
    "Background Jobs",
    "Business KPI",
    "Alerts",
)


class MonitoringCenterError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


def ensure_monitoring() -> dict[str, Any]:
    return {"ready": True, "read_only": True}


def application_health() -> dict[str, Any]:
    ensure_monitoring()
    app = current_app._get_current_object()
    evaluation = HealthPlatformService.evaluate()
    production, _status = health_payload(app)
    application = HealthPlatformService.check_application()
    return {
        "report": "application_health",
        "read_only": True,
        "status": evaluation["status"],
        "components": evaluation["components"],
        "startup": application,
        "production_probe": production,
    }


def database_health() -> dict[str, Any]:
    ensure_monitoring()
    app = current_app._get_current_object()
    detail = _safe(lambda: HealthPlatformService.check_database(), {"status": "DOWN"})
    migrations = _safe(lambda: verify_migrations(app), {"ready": False})
    try:
        verify_database_connection(app, retries=1, delay_seconds=0)
        connectivity = "OK"
    except Exception as exc:
        connectivity = "DOWN"
        detail = {"status": "DOWN", "error": str(exc)}
    return {
        "report": "database_health",
        "read_only": True,
        "status": detail.get("status", connectivity),
        "connectivity": connectivity,
        "detail": detail,
        "migrations": migrations,
        "engine": app.config.get("SQLALCHEMY_DATABASE_URI", "").split(":", 1)[0],
    }


def redis_health() -> dict[str, Any]:
    ensure_monitoring()
    app = current_app._get_current_object()
    ping = check_redis_health(app)
    platform = HealthPlatformService.check_redis()
    return {
        "report": "redis_health",
        "read_only": True,
        "status": ping.get("status", "DEGRADED"),
        "configured": bool(app.config.get("REDIS_URL")),
        "ping": ping,
        "platform_check": platform,
    }


def queue_health() -> dict[str, Any]:
    ensure_monitoring()
    summary = _safe(QueueOperationsService.summary, {})
    platform_queue = HealthPlatformService.check_queue()
    dead_letters = _safe(lambda: QueueOperationsService.list_dead_letters(limit=10), {})
    status = "OK"
    if summary.get("failed_jobs", 0) > 0 or summary.get("dead_letter_count", 0) > 0:
        status = "DEGRADED"
    if summary.get("queue_depth", 0) > 100:
        status = "DEGRADED"
    return {
        "report": "queue_health",
        "read_only": True,
        "status": status,
        "summary": summary,
        "platform_queue": platform_queue,
        "recent_dead_letters": dead_letters.get("dead_letters", []),
    }


def api_latency_metrics() -> dict[str, Any]:
    ensure_monitoring()
    app = current_app._get_current_object()
    MetricsPlatformService.refresh_runtime_metrics(app)
    snapshot = platform_metrics.snapshot()
    core = core_metrics.snapshot()
    histogram = snapshot.get("histograms", {}).get("api_latency_ms", {})
    avg = histogram.get("avg") or core.get("latency_ms", {}).get("average", 0)
    return {
        "report": "api_latency",
        "read_only": True,
        "average_ms": avg,
        "p95_ms": histogram.get("p95", 0),
        "count": histogram.get("count", core.get("request_count", 0)),
        "histogram": histogram,
        "core_metrics": core,
    }


def error_rate_metrics() -> dict[str, Any]:
    ensure_monitoring()
    app = current_app._get_current_object()
    MetricsPlatformService.refresh_runtime_metrics(app)
    snapshot = platform_metrics.snapshot()
    counters = snapshot.get("counters", {})
    requests_total = counters.get("http_requests_total", 0) or core_metrics.snapshot().get("request_count", 0)
    errors_total = counters.get("http_errors_total", 0) or core_metrics.snapshot().get("error_count", 0)
    rate = round((errors_total / requests_total) * 100, 2) if requests_total else 0.0
    return {
        "report": "error_rate",
        "read_only": True,
        "requests_total": requests_total,
        "errors_total": errors_total,
        "error_rate_percent": rate,
        "authentication_failures": counters.get("authentication_failures_total", 0),
        "integration_failures": counters.get("integration_failures_total", 0),
    }


def background_jobs_status() -> dict[str, Any]:
    ensure_monitoring()
    runner = background_tasks.snapshot()
    scheduled = _safe(
        lambda: ScheduledJob.query.order_by(ScheduledJob.job_code.asc()).all(),
        [],
    )
    recent_runs = _safe(
        lambda: ScheduledJobRun.query.order_by(ScheduledJobRun.started_at.desc()).limit(10).all(),
        [],
    )
    enabled = sum(1 for job in scheduled if job.status == "ENABLED")
    return {
        "report": "background_jobs",
        "read_only": True,
        "runner": runner,
        "scheduled_jobs_total": len(scheduled),
        "scheduled_jobs_enabled": enabled,
        "scheduled_jobs": [row.to_dict() for row in scheduled[:20]],
        "recent_runs": [row.to_dict() for row in recent_runs],
    }


def business_kpi_snapshot() -> dict[str, Any]:
    ensure_monitoring()
    app = current_app._get_current_object()
    observability = MetricsPlatformService.get_business_metrics(app)
    kpi = KPIEngineService.compute_monthly(persist=False)
    return {
        "report": "business_kpi",
        "read_only": True,
        "observability": observability,
        "kpi_engine": kpi,
    }


def alerts_overview(limit: int = 50) -> dict[str, Any]:
    ensure_monitoring()
    alerts = AlertEngine.list_alerts(limit=limit)
    open_count = sum(1 for item in alerts.get("alerts", []) if item.get("status") == "OPEN")
    return {
        "report": "alerts",
        "read_only": True,
        "open_alerts": open_count,
        "alerts_total": alerts.get("count", 0),
        "rules": ALERT_RULES,
        "alerts": alerts.get("alerts", []),
    }


def monitoring_readiness_report() -> dict[str, Any]:
    dashboard = dashboard_payload()
    return {
        "generated_at": dashboard.get("generated_at"),
        "phase": "5.2",
        "sprint": "Monitoring Center",
        "platform": dashboard["platform"],
        "status": dashboard["status"],
        "summary": dashboard["summary"],
        "features": list(FEATURES),
        "sections": {
            "application": application_health(),
            "queues": queue_health(),
            "database": database_health(),
            "redis": redis_health(),
            "latency": api_latency_metrics(),
            "errors": error_rate_metrics(),
            "jobs": background_jobs_status(),
            "kpi": business_kpi_snapshot(),
            "alerts": alerts_overview(limit=10),
        },
    }


def dashboard_payload() -> dict[str, Any]:
    ensure_monitoring()
    app_health = application_health()
    queue = queue_health()
    database = database_health()
    redis = redis_health()
    latency = api_latency_metrics()
    errors = error_rate_metrics()
    jobs = background_jobs_status()
    kpi = business_kpi_snapshot()
    alerts = alerts_overview(limit=5)
    statuses = [
        app_health["status"],
        queue["status"],
        database["status"],
        redis["status"],
    ]
    overall = "OK"
    if "DOWN" in statuses:
        overall = "DOWN"
    elif "DEGRADED" in statuses:
        overall = "DEGRADED"
    from datetime import datetime

    return {
        "platform": "Monitoring Center",
        "phase": "5.2",
        "sprint": "Monitoring Center",
        "status": overall,
        "read_only": True,
        "generated_at": datetime.utcnow().isoformat(),
        "summary": {
            "application_status": app_health["status"],
            "queue_depth": queue["summary"].get("queue_depth", 0),
            "database_status": database["status"],
            "redis_status": redis["status"],
            "average_latency_ms": latency["average_ms"],
            "error_rate_percent": errors["error_rate_percent"],
            "background_pending": jobs["runner"].get("pending", 0),
            "scheduled_jobs": jobs["scheduled_jobs_total"],
            "orders_total": kpi["observability"].get("orders_created_total", 0),
            "open_alerts": alerts["open_alerts"],
        },
        "features": list(FEATURES),
    }
