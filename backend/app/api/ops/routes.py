from flask import Blueprint
from datetime import datetime
from sqlalchemy import text

from app.extensions.db import db
from app.models.user import User
from app.models.patient import Patient
from app.models.order import Order
from app.models.sample_tracking import SampleTracking
from app.models.test_result import TestResult
from app.models.invoice import Invoice
from app.models.payment import Payment


ops_bp = Blueprint(
    "ops",
    __name__,
    url_prefix="/api/v1/ops"
)


@ops_bp.route("/health")
def health():
    try:
        db.session.execute(text("SELECT 1"))
        database = "ok"
    except Exception as e:
        database = str(e)

    return {
        "service": "dxcon",
        "status": "ok",
        "database": database,
        "time": datetime.utcnow().isoformat()
    }


@ops_bp.route("/production-check")
def production_check():
    return {
        "users": User.query.count(),
        "patients": Patient.query.count(),
        "orders": Order.query.count(),
        "samples": SampleTracking.query.count(),
        "results": TestResult.query.count(),
        "invoices": Invoice.query.count(),
        "payments": Payment.query.count()
    }
