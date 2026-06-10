from flask import Blueprint

from app.models.patient import Patient
from app.models.company import Company
from app.models.order import Order
from app.models.invoice import Invoice
from app.models.payment import Payment


dashboard_bp = Blueprint(
    "dashboard",
    __name__,
    url_prefix="/api/v1/dashboard"
)


@dashboard_bp.route("/summary", methods=["GET"])
def summary():

    patients = Patient.query.count()
    companies = Company.query.count()
    orders = Order.query.count()
    invoices = Invoice.query.count()
    payments = Payment.query.count()

    completed_orders = Order.query.filter_by(
        status="COMPLETED"
    ).count()

    pending_orders = Order.query.filter_by(
        status="PENDING"
    ).count()

    processing_orders = Order.query.filter_by(
        status="PROCESSING"
    ).count()

    paid_invoices = Invoice.query.filter_by(
        payment_status="PAID"
    ).count()

    unpaid_invoices = Invoice.query.filter_by(
        payment_status="UNPAID"
    ).count()

    revenue = 0

    for payment in Payment.query.all():
        revenue += payment.amount or 0

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
        "revenue": revenue
    }
