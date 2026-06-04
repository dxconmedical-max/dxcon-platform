from flask import Blueprint, request

from app.extensions.db import db
from app.models.invoice import Invoice


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
        payment_status=data.get(
            "payment_status",
            "UNPAID"
        )
    )

    db.session.add(invoice)
    db.session.commit()

    return {
        "message": "Invoice created successfully",
        "invoice": invoice.to_dict()
    }, 201
