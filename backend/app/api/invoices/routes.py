from flask import Blueprint, request
import uuid

from app.extensions.db import db
from app.models.invoice import Invoice
from app.models.order import Order
from app.models.company import Company


invoices_bp = Blueprint(
    "invoices",
    __name__,
    url_prefix="/api/v1/invoices"
)


@invoices_bp.route("", methods=["GET"])
def get_invoices():

    invoices = Invoice.query.all()

    return {
        "count": len(invoices),
        "invoices": [
            invoice.to_dict()
            for invoice in invoices
        ]
    }


@invoices_bp.route("", methods=["POST"])
def create_invoice():

    data = request.get_json()

    invoice = Invoice(
        invoice_no=data.get("invoice_no"),
        company_id=data.get("company_id"),
        order_id=data.get("order_id"),
        total_amount=data.get("total_amount", 0),
        payment_status=data.get("payment_status", "UNPAID")
    )

    db.session.add(invoice)
    db.session.commit()

    return {
        "message": "Invoice created successfully",
        "invoice": invoice.to_dict()
    }, 201


@invoices_bp.route("/generate/<order_id>", methods=["POST"])
def generate_invoice(order_id):

    order = Order.query.get(order_id)

    if not order:
        return {
            "error": "Order not found"
        }, 404

    company = Company.query.first()

    if not company:
        return {
            "error": "Company not found"
        }, 404

    invoice = Invoice(
        invoice_no=f"INV-{str(uuid.uuid4())[:8]}",
        company_id=company.id,
        order_id=order.id,
        total_amount=order.total_amount or 0,
        payment_status="UNPAID"
    )

    db.session.add(invoice)
    db.session.commit()

    return {
        "message": "Invoice generated successfully",
        "invoice": invoice.to_dict()
    }, 201
