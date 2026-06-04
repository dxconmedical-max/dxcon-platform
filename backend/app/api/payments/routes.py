from flask import Blueprint, request

from app.extensions.db import db
from app.models.payment import Payment
from app.models.invoice import Invoice


payments_bp = Blueprint(
    "payments",
    __name__,
    url_prefix="/api/v1/payments"
)


@payments_bp.route("", methods=["GET"])
def get_payments():

    payments = Payment.query.all()

    return {
        "count": len(payments),
        "payments": [
            payment.to_dict()
            for payment in payments
        ]
    }


@payments_bp.route("", methods=["POST"])
def create_payment():

    data = request.get_json()

    payment = Payment(
        invoice_id=data.get("invoice_id"),
        amount=data.get("amount"),
        payment_method=data.get(
            "payment_method",
            "BANK_TRANSFER"
        )
    )

    db.session.add(payment)

    invoice = Invoice.query.get(
        data.get("invoice_id")
    )

    if invoice:
        invoice.payment_status = "PAID"

    db.session.commit()

    return {
        "message": "Payment recorded successfully",
        "payment": payment.to_dict()
    }, 201
