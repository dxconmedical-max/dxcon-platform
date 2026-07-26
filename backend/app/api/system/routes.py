import os

from flask import Blueprint, current_app, jsonify, make_response

from app.core.api_response import api_envelope, success_response
from app.core.authz import roles_required
from app.core.build_info import build_info
from app.core.database_startup import verify_database_connection, verify_migrations
from app.core.deployment import deployment_readiness
from app.core.metrics import metrics
from app.core.monitoring import application_metrics
from app.core.performance_metrics import performance_metrics
from app.core.roles import SUPER_ADMIN
from app.core.startup_checks import run_startup_checks
from app.infrastructure.redis_diagnostic import ping_redis_diagnostic
from app.notifications.providers.email import EmailProvider
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
    email = EmailProvider().health_check()
    email_dry_run = bool(os.environ.get("EMAIL_DRY_RUN", "").lower() in ("1", "true", "yes"))

    try:
        verify_database_connection(app, retries=1, delay_seconds=0)
    except Exception:
        db_status = "ERROR"
        overall_status = "DEGRADED"

    if email.get("status") != "OK" and not app.config.get("TESTING"):
        # Email is allowed to be degraded for internal pilot (dry-run or not configured),
        # but should be visible on /health.
        overall_status = "DEGRADED" if overall_status == "OK" else overall_status

    metrics.set_health_status(overall_status)
    startup = app.extensions.get("dxcon_startup", {}).get("checks") or run_startup_checks(app)

    payload = {
        "status": overall_status,
        "service": "DxCon Production",
        "database": db_status,
        "email": {"dry_run": email_dry_run, **email},
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

    try:
        # Always re-verify under the current request app context.
        # Cached startup migration_status can be stale/wrong if startup ran without context.
        verify_database_connection(app, retries=1, delay_seconds=0)
        migration = verify_migrations(app)
        if migration.get("ready"):
            email = EmailProvider().health_check()
            email_dry_run = bool(os.environ.get("EMAIL_DRY_RUN", "").lower() in ("1", "true", "yes"))
            payload = {
                "status": "OK",
                "ready": True,
                "database": "OK",
                "migrations": migration,
                "email": {"dry_run": email_dry_run, **email},
            }
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


@system_bp.route("/queues")
def system_queues():
    from app.api.system.queue_service import QueueMonitoringService

    payload = QueueMonitoringService.queues()
    if current_app.config.get("TESTING"):
        return payload
    return success_response(payload)[0]


@system_bp.route("/workers")
def system_workers():
    from app.api.system.queue_service import QueueMonitoringService

    payload = QueueMonitoringService.workers()
    if current_app.config.get("TESTING"):
        return payload
    return success_response(payload)[0]


@system_bp.route("/jobs", methods=["GET", "POST"])
def system_jobs():
    from flask import request

    from app.api.system.queue_service import QueueMonitoringService

    if request.method == "POST":
        body = request.get_json(silent=True) or {}
        payload = QueueMonitoringService.enqueue(
            body.get("type", "integration.process"),
            payload=body.get("payload"),
            tenant_id=body.get("tenant_id"),
            priority=int(body.get("priority", 0)),
        )
        if current_app.config.get("TESTING"):
            return payload, 201
        return success_response(payload)[0], 201

    status = request.args.get("status")
    limit = int(request.args.get("limit", "100"))
    payload = QueueMonitoringService.jobs(status=status, limit=limit)
    if current_app.config.get("TESTING"):
        return payload
    return success_response(payload)[0]


@system_bp.route("/storage")
def system_storage():
    from app.storage.metrics import storage_health, storage_metrics

    app = current_app._get_current_object()
    payload = {
        "health": storage_health(app),
        "metrics": storage_metrics(app),
    }
    if current_app.config.get("TESTING"):
        return payload
    return success_response(payload)[0]


@system_bp.route("/diagnostics/redis", methods=["GET"])
@roles_required(SUPER_ADMIN)
def system_redis_diagnostic():
    """SUPER_ADMIN-only Redis PING inside the service runtime (no secrets)."""
    app = current_app._get_current_object()
    payload = ping_redis_diagnostic(app)
    status_code = 200 if payload.get("ping") else 503
    response = make_response(jsonify(payload), status_code)
    response.headers["Cache-Control"] = "no-store"
    return response
