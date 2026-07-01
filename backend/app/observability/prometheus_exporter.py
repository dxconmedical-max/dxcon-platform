from flask import current_app

from app.observability.metrics import platform_metrics
from app.observability.metrics_registry import METRIC_DEFINITIONS


def _escape(value):
    return str(value).replace("\\", "\\\\").replace("\n", "\\n").replace('"', '\\"')


def prometheus_metrics_text(app=None):
    app = app or current_app._get_current_object()
    from app.observability.metrics_service import MetricsPlatformService

    MetricsPlatformService.refresh_runtime_metrics(app)
    snapshot = platform_metrics.snapshot()
    lines = []

    for name, meta in METRIC_DEFINITIONS.items():
        metric_type = meta.get("type", "counter")
        help_name = name.replace(".", "_")
        lines.append(f"# HELP {help_name} {meta.get('description', name)}")
        lines.append(f"# TYPE {help_name} {metric_type}")

    for key, value in snapshot["counters"].items():
        metric_name = key.split("|", 1)[0].replace(".", "_")
        lines.append(f"{metric_name} {value}")

    for key, value in snapshot["gauges"].items():
        metric_name = key.split("|", 1)[0].replace(".", "_")
        lines.append(f"{metric_name} {value}")

    for key, bucket in snapshot["histograms"].items():
        metric_name = key.split("|", 1)[0].replace(".", "_")
        lines.append(f"{metric_name}_count {bucket.get('count', 0)}")
        lines.append(f"{metric_name}_sum {bucket.get('sum', 0)}")

    return "\n".join(lines) + "\n"


def prometheus_auth_required(app):
    if app.config.get("TESTING"):
        return False
    return bool(app.config.get("PROMETHEUS_AUTH_REQUIRED", False))
