from flask import Blueprint, current_app

from app.core.api_response import api_envelope, success_response
from app.core.build_info import build_info
from app.core.database_startup import verify_database_connection, verify_migrations
from app.core.deployment import deployment_readiness
from app.core.metrics import metrics
from app.core.monitoring import application_metrics
from app.core.performance_metrics import performance_metrics
from app.core.startup_checks import run_startup_checks
from app.extensions.db import db
from app.models.invoice import Invoice
from app.models.order import Order
from app.models.patient import Patient
from app.models.payment import Payment
from app.models.sample_tracking import SampleTracking
from app.models.test_result import TestResult
from app.models.user import User

system_bp = Blueprint(
    "system",
    __name__,
    url_prefix="/api/v1/system"
)


@system_bp.route("/routes")
def routes():
    from flask import current_app

    data = []

    for rule in current_app.url_map.iter_rules():
        data.append({
            "route": str(rule),
            "endpoint": rule.endpoint,
            "methods": sorted([
                m for m in rule.methods
                if m not in ["HEAD", "OPTIONS"]
            ])
        })

    return {
        "count": len(data),
        "routes": sorted(data, key=lambda x: x["route"])
    }


@system_bp.route("/stats")
def stats():

    return {
        "users": User.query.count(),
        "patients": Patient.query.count(),
        "orders": Order.query.count(),
        "samples": SampleTracking.query.count(),
        "results": TestResult.query.count(),
        "invoices": Invoice.query.count(),
        "payments": Payment.query.count()
    }


@system_bp.route("/health")
def health():
    app = current_app._get_current_object()

    db_status = "OK"
    overall_status = "OK"

    try:
        verify_database_connection(app, retries=1, delay_seconds=0)
    except Exception:
        db_status = "ERROR"
        overall_status = "DEGRADED"

    metrics.set_health_status(overall_status)
    startup = app.extensions.get("dxcon_startup", {}).get("checks") or run_startup_checks(app)

    payload = {
        "status": overall_status,
        "service": "DxCon Production",
        "database": db_status,
        "build": build_info(),
        "startup": startup,
    }

    if app.config.get("TESTING"):
        return payload
    return success_response(payload)[0]


def _live_payload():
    payload = {"status": "OK", "alive": True}
    if current_app.config.get("TESTING"):
        return payload
    return success_response(payload)[0]


@system_bp.route("/live")
def live():
    return _live_payload()


@system_bp.route("/liveness")
def liveness():
    return _live_payload()


def _ready_response():
    app = current_app._get_current_object()
    migration = app.extensions.get("dxcon_deployment", {}).get("migration_status", {})

    try:
        verify_database_connection(app, retries=1, delay_seconds=0)
        migration = migration or verify_migrations(app)
        if migration.get("ready"):
            payload = {"status": "OK", "ready": True, "database": "OK", "migrations": migration}
            if app.config.get("TESTING"):
                return payload
            return success_response(payload)[0]
        payload = {"status": "DEGRADED", "ready": False, "migrations": migration}
        if app.config.get("TESTING"):
            return payload, 503
        return api_envelope(False, data=payload, error={"code": "NOT_READY", "message": "Service not ready"}), 503
    except Exception as exc:
        payload = {"status": "ERROR", "ready": False, "error": str(exc)}
        if app.config.get("TESTING"):
            return payload, 503
        return api_envelope(False, data=payload, error={"code": "STARTUP_ERROR", "message": str(exc)}), 503


@system_bp.route("/ready")
def ready():
    return _ready_response()


@system_bp.route("/readiness")
def readiness():
    return _ready_response()


@system_bp.route("/version")
def version():
    payload = build_info()
    if current_app.config.get("TESTING"):
        return payload
    return success_response(payload)[0]


@system_bp.route("/build")
def build():
    app = current_app._get_current_object()
    payload = {
        **build_info(),
        "readiness": deployment_readiness(app),
    }
    if app.config.get("TESTING"):
        return payload
    return success_response(payload)[0]


@system_bp.route("/metrics")
def system_metrics():
    from flask import current_app

    app = current_app._get_current_object()
    payload = application_metrics(app)
    legacy = metrics.snapshot()
    payload["legacy"] = legacy
    payload.update(legacy)
    return payload


@system_bp.route("/performance")
def system_performance():
    from flask import current_app

    return performance_metrics.snapshot(current_app)


@system_bp.route("/backup-status")
def backup_status():
    return {
        "database": "PostgreSQL",
        "provider": "Render",
        "backup_policy": "Enable daily backup in Render PostgreSQL dashboard",
        "recommended_retention": "7-30 days",
        "status": "MANUAL_CHECK_REQUIRED"
    }
