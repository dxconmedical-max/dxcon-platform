from flask import Blueprint, request

from app.services.payment_gateway_service import (
    PaymentGatewayError,
    PaymentGatewayService,
    PaymentService,
    RefundService,
    WebhookService,
)


payments_bp = Blueprint(
    "payments",
    __name__,
    url_prefix="/api/v1/payments",
)


def _client_ip():
    return request.remote_addr or ""


def _actor_email():
    return request.headers.get("X-User-Email", "SYSTEM")


@payments_bp.route("", methods=["GET"])
def get_payments():
    payload = PaymentService.list_payments(
        invoice_id=request.args.get("invoice_id"),
        provider=request.args.get("provider"),
    )
    return payload


@payments_bp.route("/create", methods=["POST"])
def create_payment():
    data = request.get_json(silent=True) or {}
    try:
        payload = PaymentService.create_payment(
            data,
            actor_email=_actor_email(),
            ip_address=_client_ip(),
        )
    except PaymentGatewayError as exc:
        return {"error": exc.message}, exc.status_code
    return {"message": "Payment created", **payload}, 201


@payments_bp.route("/webhook", methods=["POST"])
def payment_webhook():
    data = request.get_json(silent=True) or {}
    provider = data.get("provider") or request.headers.get("X-Payment-Provider", "VNPAY")
    try:
        payload = WebhookService.process_webhook(
            provider,
            data,
            headers=dict(request.headers),
            actor_email=_actor_email(),
            ip_address=_client_ip(),
        )
    except PaymentGatewayError as exc:
        return {"error": exc.message}, exc.status_code
    return {"message": "Webhook processed", **payload}


@payments_bp.route("/refund", methods=["POST"])
def payment_refund():
    data = request.get_json(silent=True) or {}
    try:
        payload = RefundService.process_refund(
            data,
            actor_email=_actor_email(),
            ip_address=_client_ip(),
        )
    except PaymentGatewayError as exc:
        return {"error": exc.message}, exc.status_code
    return {"message": "Refund processed", **payload}


@payments_bp.route("/history", methods=["GET"])
def payment_history():
    payload = PaymentService.get_history(
        invoice_id=request.args.get("invoice_id"),
        provider=request.args.get("provider"),
    )
    return payload


@payments_bp.route("/providers", methods=["GET"])
def payment_providers():
    return {"providers": PaymentGatewayService.supported_providers()}
