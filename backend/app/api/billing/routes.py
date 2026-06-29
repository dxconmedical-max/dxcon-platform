from flask import Blueprint, request

from app.services.billing_service import BillingError, BillingService
from app.services.commission_service import CommissionService
from app.services.refund_service import RefundService, RefundServiceError
from app.services.settlement_service import SettlementError, SettlementService


billing_bp = Blueprint(
    "billing",
    __name__,
    url_prefix="/api/v1/billing",
)


def _client_ip():
    return request.remote_addr or ""


def _actor_email():
    return request.headers.get("X-User-Email", "SYSTEM")


@billing_bp.route("/invoices", methods=["GET"])
def list_invoices():
    invoices = BillingService.list_invoices(
        partner_id=request.args.get("partner_id"),
        status=request.args.get("status"),
    )
    return {"count": len(invoices), "invoices": [inv.to_dict() for inv in invoices]}


@billing_bp.route("/invoices", methods=["POST"])
def create_invoice():
    data = request.get_json(silent=True) or {}
    medical_order_id = data.get("medical_order_id")
    if not medical_order_id:
        return {"error": "medical_order_id is required"}, 400
    try:
        invoice = BillingService.create_invoice_from_medical_order(
            medical_order_id,
            actor_email=_actor_email(),
            ip_address=_client_ip(),
        )
    except BillingError as exc:
        return {"error": exc.message}, exc.status_code
    return {"message": "Invoice created", "invoice": invoice.to_dict()}, 201


@billing_bp.route("/invoices/<invoice_id>", methods=["GET"])
def get_invoice(invoice_id):
    try:
        payload = BillingService.get_invoice_detail(invoice_id)
    except BillingError as exc:
        return {"error": exc.message}, exc.status_code
    return payload


@billing_bp.route("/payments", methods=["GET"])
def list_payments():
    payments = BillingService.list_payments(invoice_id=request.args.get("invoice_id"))
    return {"count": len(payments), "payments": [p.to_dict() for p in payments]}


@billing_bp.route("/payments", methods=["POST"])
def record_payment():
    data = request.get_json(silent=True) or {}
    invoice_id = data.get("invoice_id")
    if not invoice_id:
        return {"error": "invoice_id is required"}, 400
    try:
        payment, invoice = BillingService.record_payment(
            invoice_id,
            amount=data.get("amount"),
            payment_method=data.get("payment_method", "BANK_TRANSFER"),
            transaction_ref=data.get("transaction_ref"),
            actor_email=_actor_email(),
            ip_address=_client_ip(),
        )
    except BillingError as exc:
        return {"error": exc.message}, exc.status_code
    return {
        "message": "Payment recorded",
        "payment": payment.to_dict(),
        "invoice": invoice.to_dict(),
    }, 201


@billing_bp.route("/refunds", methods=["GET"])
def list_refunds():
    refunds = RefundService.list_refunds(invoice_id=request.args.get("invoice_id"))
    return {"count": len(refunds), "refunds": [r.to_dict() for r in refunds]}


@billing_bp.route("/refunds", methods=["POST"])
def process_refund():
    data = request.get_json(silent=True) or {}
    invoice_id = data.get("invoice_id")
    if not invoice_id:
        return {"error": "invoice_id is required"}, 400
    try:
        refund, invoice = RefundService.process_refund(
            invoice_id,
            reason=data.get("reason"),
            amount=data.get("amount"),
            actor_email=_actor_email(),
            ip_address=_client_ip(),
        )
    except RefundServiceError as exc:
        return {"error": exc.message}, exc.status_code
    return {
        "message": "Refund processed",
        "refund": refund.to_dict(),
        "invoice": invoice.to_dict(),
    }, 201


@billing_bp.route("/settlements", methods=["GET"])
def list_settlements():
    settlements = SettlementService.list_settlements(
        partner_id=request.args.get("partner_id")
    )
    return {
        "count": len(settlements),
        "settlements": [s.to_dict() for s in settlements],
    }


@billing_bp.route("/settlements", methods=["POST"])
def create_settlement():
    data = request.get_json(silent=True) or {}
    partner_id = data.get("partner_id")
    if not partner_id:
        return {"error": "partner_id is required"}, 400
    try:
        if data.get("invoice_id"):
            CommissionService.calculate_for_invoice(
                data["invoice_id"],
                partner_id=partner_id,
                collector_id=data.get("collector_id"),
                doctor_id=data.get("doctor_id"),
            )
        settlement = SettlementService.create_settlement(
            partner_id,
            period_start=data.get("period_start"),
            period_end=data.get("period_end"),
            actor_email=_actor_email(),
            ip_address=_client_ip(),
        )
    except SettlementError as exc:
        return {"error": exc.message}, exc.status_code
    return {"message": "Settlement created", "settlement": settlement.to_dict()}, 201


@billing_bp.route("/settlements/<settlement_id>", methods=["GET"])
def get_settlement(settlement_id):
    try:
        payload = SettlementService.get_settlement_detail(settlement_id)
    except SettlementError as exc:
        return {"error": exc.message}, exc.status_code
    return payload


@billing_bp.route("/settlements/<settlement_id>/finalize", methods=["POST"])
def finalize_settlement(settlement_id):
    try:
        settlement = SettlementService.finalize_settlement(
            settlement_id,
            actor_email=_actor_email(),
            ip_address=_client_ip(),
        )
    except SettlementError as exc:
        return {"error": exc.message}, exc.status_code
    return {"message": "Settlement finalized", "settlement": settlement.to_dict()}


@billing_bp.route("/commissions", methods=["GET"])
def list_commissions():
    commissions = CommissionService.list_commissions(
        partner_id=request.args.get("partner_id"),
        invoice_id=request.args.get("invoice_id"),
    )
    return {
        "count": len(commissions),
        "commissions": [c.to_dict() for c in commissions],
    }


@billing_bp.route("/commissions/rules", methods=["GET"])
def list_commission_rules():
    rules = CommissionService.list_rules()
    return {"count": len(rules), "rules": [r.to_dict() for r in rules]}


@billing_bp.route("/commissions/calculate", methods=["POST"])
def calculate_commissions():
    data = request.get_json(silent=True) or {}
    invoice_id = data.get("invoice_id")
    if not invoice_id:
        return {"error": "invoice_id is required"}, 400
    try:
        entries = CommissionService.calculate_for_invoice(
            invoice_id,
            partner_id=data.get("partner_id"),
            collector_id=data.get("collector_id"),
            doctor_id=data.get("doctor_id"),
        )
    except Exception as exc:
        message = getattr(exc, "message", str(exc))
        status = getattr(exc, "status_code", 400)
        return {"error": message}, status
    return {
        "message": "Commissions calculated",
        "commissions": [entry.to_dict() for entry in entries],
    }
