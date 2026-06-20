from flask import Blueprint
from app.models.user import User
from app.models.patient import Patient
from app.models.order import Order
from app.models.sample_tracking import SampleTracking
from app.models.test_result import TestResult
from app.models.invoice import Invoice
from app.models.payment import Payment
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

    return {
        "status": "OK",
        "service": "DxCon Production",
        "database": "PostgreSQL"
    }


@system_bp.route("/backup-status")
def backup_status():
    return {
        "database": "PostgreSQL",
        "provider": "Render",
        "backup_policy": "Enable daily backup in Render PostgreSQL dashboard",
        "recommended_retention": "7-30 days",
        "status": "MANUAL_CHECK_REQUIRED"
    }
