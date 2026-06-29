from flask import Blueprint

from app.core.build_info import build_info
from app.core.database_startup import verify_database_connection, verify_migrations
from app.core.deployment import deployment_readiness
from app.core.metrics import metrics
from app.core.monitoring import application_metrics
from app.core.performance_metrics import performance_metrics
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
    from flask import current_app

    db_status = "OK"
    overall_status = "OK"

    try:
        verify_database_connection(current_app._get_current_object(), retries=1, delay_seconds=0)
    except Exception:
        db_status = "ERROR"
        overall_status = "DEGRADED"

    metrics.set_health_status(overall_status)

    return {
        "status": overall_status,
        "service": "DxCon Production",
        "database": db_status,
        "build": build_info(),
    }


@system_bp.route("/live")
def live():
    return {
        "status": "OK",
        "alive": True,
    }


@system_bp.route("/ready")
def ready():
    from flask import current_app

    app = current_app._get_current_object()
    migration = app.extensions.get("dxcon_deployment", {}).get("migration_status", {})

    try:
        verify_database_connection(app, retries=1, delay_seconds=0)
        migration = migration or verify_migrations(app)
        if migration.get("ready"):
            return {"status": "OK", "ready": True, "database": "OK", "migrations": migration}
        return {"status": "DEGRADED", "ready": False, "migrations": migration}, 503
    except Exception as exc:
        return {"status": "ERROR", "ready": False, "error": str(exc)}, 503


@system_bp.route("/version")
def version():
    return build_info()


@system_bp.route("/build")
def build():
    from flask import current_app

    return {
        **build_info(),
        "readiness": deployment_readiness(current_app._get_current_object()),
    }


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
