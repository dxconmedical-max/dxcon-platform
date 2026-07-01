from flask import Blueprint, current_app, request

from app.observability.alert_engine import AlertEngine
from app.observability.health_service import HealthPlatformService
from app.observability.metrics_exporter import (
    export_business_payload,
    export_metrics_payload,
    export_system_payload,
)
from app.observability.prometheus_exporter import prometheus_auth_required, prometheus_metrics_text


observability_metrics_bp = Blueprint("observability_metrics", __name__, url_prefix="/api/v1/metrics")
observability_prometheus_bp = Blueprint("observability_prometheus", __name__)
observability_health_root_bp = Blueprint("observability_health_root", __name__)
observability_alerts_bp = Blueprint("observability_alerts", __name__, url_prefix="/api/v1/alerts")


@observability_metrics_bp.route("", methods=["GET"])
def metrics_all():
    return export_metrics_payload(current_app._get_current_object())


@observability_metrics_bp.route("/system", methods=["GET"])
def metrics_system():
    return export_system_payload(current_app._get_current_object())


@observability_metrics_bp.route("/business", methods=["GET"])
def metrics_business():
    return export_business_payload(current_app._get_current_object())


@observability_prometheus_bp.route("/metrics/prometheus", methods=["GET"])
def prometheus_metrics():
    app = current_app._get_current_object()
    if prometheus_auth_required(app):
        token = request.headers.get("Authorization", "")
        expected = app.config.get("PROMETHEUS_AUTH_TOKEN")
        if expected and token != f"Bearer {expected}":
            return {"error": "Unauthorized"}, 401
    return prometheus_metrics_text(app), 200, {"Content-Type": "text/plain; version=0.0.4"}


@observability_health_root_bp.route("/health", methods=["GET"])
def root_health():
    payload, status = HealthPlatformService.health()
    return payload, status


@observability_health_root_bp.route("/ready", methods=["GET"])
def root_ready():
    payload, status = HealthPlatformService.ready()
    return payload, status


@observability_health_root_bp.route("/live", methods=["GET"])
def root_live():
    return HealthPlatformService.live()


@observability_alerts_bp.route("/test", methods=["POST"])
def test_alert():
    return AlertEngine.test_alert(request.get_json(silent=True) or {}), 201

