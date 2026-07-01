from app.core.metrics import metrics as core_metrics
from app.core.monitoring import application_metrics
from app.core.performance_metrics import performance_metrics
from app.extensions.db import db
from app.models.observability_platform import ObsMetricSnapshot
from app.models.order import Order
from app.models.test_result import TestResult
from app.observability.metrics import platform_metrics
from app.observability.metrics_registry import list_metric_definitions


class MetricsPlatformService:
    @staticmethod
    def refresh_runtime_metrics(app):
        try:
            from app.models.integration_platform import IntegrationJob
            from app.models.notification_center import NCNotification

            platform_metrics.set_gauge("queue_depth", IntegrationJob.query.filter_by(status="QUEUED").count())
            sent = NCNotification.query.filter_by(status="SENT").all()
            if sent:
                avg_latency = sum(row.latency_ms or 0 for row in sent) / len(sent)
                platform_metrics.set_gauge("notification_latency_ms", round(avg_latency, 2))
        except Exception:
            platform_metrics.set_gauge("queue_depth", 0)

        perf = performance_metrics.snapshot(app)
        platform_metrics.set_gauge("database_latency_ms", perf.get("average_query_ms", 0))
        platform_metrics.inc("orders_created_total", Order.query.count())
        platform_metrics.inc("results_approved_total", TestResult.query.filter_by(approval_status="APPROVED").count())
        platform_metrics.inc("critical_results_total", 0)

    @staticmethod
    def get_metrics(app):
        MetricsPlatformService.refresh_runtime_metrics(app)
        core = core_metrics.snapshot()
        platform = platform_metrics.snapshot()
        monitoring = application_metrics(app)
        return {
            "definitions": list_metric_definitions(),
            "core": core,
            "platform": platform,
            "monitoring": monitoring,
        }

    @staticmethod
    def get_system_metrics(app):
        MetricsPlatformService.refresh_runtime_metrics(app)
        monitoring = application_metrics(app)
        return {
            "requests": core_metrics.snapshot(),
            "performance": monitoring.get("performance"),
            "memory_mb": monitoring.get("memory_mb"),
            "cpu": monitoring.get("cpu"),
            "database": monitoring.get("database"),
            "queue": monitoring.get("queue"),
            "platform": platform_metrics.snapshot(),
        }

    @staticmethod
    def get_business_metrics(app):
        MetricsPlatformService.refresh_runtime_metrics(app)
        return {
            "orders_created_total": platform_metrics.snapshot()["counters"].get("orders_created_total", 0),
            "results_approved_total": platform_metrics.snapshot()["counters"].get("results_approved_total", 0),
            "critical_results_total": platform_metrics.snapshot()["counters"].get("critical_results_total", 0),
            "integration_failures_total": platform_metrics.snapshot()["counters"].get("integration_failures_total", 0),
            "login_success_rate": platform_metrics.snapshot()["gauges"].get("login_success_rate", 100.0),
            "notification_latency_ms": platform_metrics.snapshot()["gauges"].get("notification_latency_ms", 0),
            "webhook_latency_ms": platform_metrics.snapshot()["histograms"].get("webhook_latency_ms", {}),
        }

    @staticmethod
    def record_http_request(latency_ms, status_code):
        platform_metrics.inc("http_requests_total")
        platform_metrics.observe("api_latency_ms", latency_ms)
        core_metrics.record_request(latency_ms)
        if status_code >= 400:
            core_metrics.record_error()

    @staticmethod
    def record_auth_failure():
        platform_metrics.inc("authentication_failures_total")

    @staticmethod
    def record_login_success():
        platform_metrics.set_gauge("login_success_rate", 100.0)

    @staticmethod
    def record_integration_failure():
        platform_metrics.inc("integration_failures_total")

    @staticmethod
    def persist_snapshot(name, value, metric_type="counter", labels=None):
        import json

        row = ObsMetricSnapshot(
            metric_name=name,
            metric_type=metric_type,
            value=float(value),
            labels_json=json.dumps(labels or {}),
        )
        db.session.add(row)
        db.session.commit()
        return row.to_dict()
