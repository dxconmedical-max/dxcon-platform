from flask import Blueprint, request

from app.core.statuses import (
    DASHBOARD_ROLE_ADMIN,
    DASHBOARD_ROLE_CLINIC,
    DASHBOARD_ROLE_COLLECTOR,
    DASHBOARD_ROLE_EXECUTIVE,
    DASHBOARD_ROLE_LAB,
    DASHBOARD_ROLE_PARTNER,
)
from app.models.company import Company
from app.models.invoice import Invoice
from app.models.order import Order
from app.models.patient import Patient
from app.models.payment import Payment
from app.services.dashboard_platform_service import DashboardPlatformService


dashboard_bp = Blueprint(
    "dashboard",
    __name__,
    url_prefix="/api/v1/dashboard",
)


def _date_args():
    return request.args.get("date_from"), request.args.get("date_to")


def _pagination_args():
    return (
        max(int(request.args.get("page", 1)), 1),
        min(max(int(request.args.get("page_size", 20)), 1), 200),
    )


def _filters():
    return {
        key: request.args.get(key)
        for key in ("partner_id", "collector_id", "clinic_id", "status")
        if request.args.get(key)
    }


@dashboard_bp.route("/summary", methods=["GET"])
def summary():
    patients = Patient.query.count()
    companies = Company.query.count()
    orders = Order.query.count()
    invoices = Invoice.query.count()
    payments = Payment.query.count()

    completed_orders = Order.query.filter_by(status="COMPLETED").count()
    pending_orders = Order.query.filter_by(status="PENDING").count()
    processing_orders = Order.query.filter_by(status="PROCESSING").count()
    paid_invoices = Invoice.query.filter_by(payment_status="PAID").count()
    unpaid_invoices = Invoice.query.filter_by(payment_status="UNPAID").count()

    revenue = sum(payment.amount or 0 for payment in Payment.query.all())

    return {
        "patients": patients,
        "companies": companies,
        "orders": orders,
        "completed_orders": completed_orders,
        "pending_orders": pending_orders,
        "processing_orders": processing_orders,
        "invoices": invoices,
        "paid_invoices": paid_invoices,
        "unpaid_invoices": unpaid_invoices,
        "payments": payments,
        "revenue": revenue,
    }


@dashboard_bp.route("/executive", methods=["GET"])
def executive_dashboard():
    date_from, date_to = _date_args()
    page, page_size = _pagination_args()
    return DashboardPlatformService.get_dashboard(
        DASHBOARD_ROLE_EXECUTIVE,
        date_from,
        date_to,
        page=page,
        page_size=page_size,
        filters=_filters(),
    )


@dashboard_bp.route("/admin", methods=["GET"])
def admin_dashboard():
    date_from, date_to = _date_args()
    page, page_size = _pagination_args()
    return DashboardPlatformService.get_dashboard(
        DASHBOARD_ROLE_ADMIN,
        date_from,
        date_to,
        page=page,
        page_size=page_size,
        filters=_filters(),
    )


@dashboard_bp.route("/lab", methods=["GET"])
def lab_dashboard():
    date_from, date_to = _date_args()
    page, page_size = _pagination_args()
    return DashboardPlatformService.get_dashboard(
        DASHBOARD_ROLE_LAB,
        date_from,
        date_to,
        page=page,
        page_size=page_size,
        filters=_filters(),
    )


@dashboard_bp.route("/clinic", methods=["GET"])
def clinic_dashboard():
    date_from, date_to = _date_args()
    page, page_size = _pagination_args()
    return DashboardPlatformService.get_dashboard(
        DASHBOARD_ROLE_CLINIC,
        date_from,
        date_to,
        page=page,
        page_size=page_size,
        filters=_filters(),
    )


@dashboard_bp.route("/partner", methods=["GET"])
def partner_dashboard():
    date_from, date_to = _date_args()
    page, page_size = _pagination_args()
    return DashboardPlatformService.get_dashboard(
        DASHBOARD_ROLE_PARTNER,
        date_from,
        date_to,
        page=page,
        page_size=page_size,
        filters=_filters(),
    )


@dashboard_bp.route("/collector", methods=["GET"])
def collector_dashboard():
    date_from, date_to = _date_args()
    page, page_size = _pagination_args()
    return DashboardPlatformService.get_dashboard(
        DASHBOARD_ROLE_COLLECTOR,
        date_from,
        date_to,
        page=page,
        page_size=page_size,
        filters=_filters(),
    )
