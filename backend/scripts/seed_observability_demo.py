import json
import uuid
from datetime import datetime, timedelta

from app.extensions.db import db
from app.models.observability_platform import (
    AuditEvent,
    ObsAlert,
    ObsHealthEvent,
    ObsMetricSnapshot,
)
from app.observability.alert_engine import AlertEngine
from app.observability.audit_service import AuditTimelineService
from app.observability.health_service import HealthPlatformService
from app.observability.metrics import platform_metrics
from app.observability.metrics_service import MetricsPlatformService


def seed_observability_demo():
    AuditTimelineService.ensure_default_timeline()

    if ObsMetricSnapshot.query.count() >= 20:
        return {
            "seeded": False,
            "metrics": ObsMetricSnapshot.query.count(),
            "audit_events": AuditEvent.query.count(),
            "alerts": ObsAlert.query.count(),
            "health_events": ObsHealthEvent.query.count(),
        }

    metric_names = [
        "http_requests_total",
        "api_latency_ms",
        "database_latency_ms",
        "queue_depth",
        "webhook_latency_ms",
        "notification_latency_ms",
        "job_execution_ms",
        "authentication_failures_total",
        "orders_created_total",
        "results_approved_total",
        "critical_results_total",
        "integration_failures_total",
    ]
    for index, name in enumerate(metric_names):
        MetricsPlatformService.persist_snapshot(name, float(10 + index), labels={"source": "demo"})
        if name.endswith("_ms"):
            platform_metrics.observe(name, float(20 + index))
        else:
            platform_metrics.inc(name, float(index + 1))

    components = HealthPlatformService.COMPONENTS
    for index, component in enumerate(components):
        HealthPlatformService.record_event(component, "OK" if index % 4 else "DEGRADED", {"seed": True})

    event_types = AuditTimelineService.list_events(limit=1)["event_types"]
    for index, event_type in enumerate(event_types):
        AuditTimelineService.record(
            event_type=event_type,
            action="demo_action",
            actor={"actor_code": f"DEMO-ACTOR-{index}", "display_name": f"Demo User {index}"},
            resource={"resource_code": f"DEMO-RES-{index}", "resource_id": str(index), "resource_type": event_type},
            detail={"seed": True},
        )

    AlertEngine.test_alert({"rule_code": "HIGH_API_LATENCY", "message": "Demo latency alert"})
    AlertEngine.test_alert({"rule_code": "QUEUE_BACKLOG", "message": "Demo queue backlog"})
    AlertEngine.evaluate_rules()
    platform_metrics.set_gauge("queue_depth", 12.0)

    return {
        "seeded": True,
        "metrics": ObsMetricSnapshot.query.count(),
        "audit_events": AuditEvent.query.count(),
        "alerts": ObsAlert.query.count(),
        "health_events": ObsHealthEvent.query.count(),
    }


if __name__ == "__main__":
    from app import create_app

    app = create_app()
    with app.app_context():
        db.create_all()
        print(seed_observability_demo())
