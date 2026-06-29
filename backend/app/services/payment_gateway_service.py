import json
import uuid
from datetime import datetime

from app.core.audit import write_audit
from app.core.statuses import (
    PAYMENT_GATEWAY_COMPLETED,
    PAYMENT_GATEWAY_FAILED,
    PAYMENT_GATEWAY_PENDING,
    PAYMENT_GATEWAY_REFUNDED,
    PAYMENT_PROVIDER_MOMO,
    PAYMENT_PROVIDER_STRIPE,
    PAYMENT_PROVIDER_VNPAY,
    PAYMENT_REFUND_COMPLETED,
    PAYMENT_REFUND_PENDING,
)
from app.extensions.db import db
from app.models.invoice import Invoice
from app.models.payment import Payment
from app.models.payment_method import PaymentMethod
from app.models.payment_refund import Refund
from app.models.payment_transaction import PaymentTransaction
from app.models.payment_webhook import PaymentWebhook


class PaymentGatewayError(Exception):

    def __init__(self, message, status_code=400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class BasePaymentProvider:

    provider_code = "BASE"

    def create_payment(self, amount, currency="VND", metadata=None):
        external_id = f"{self.provider_code}-{uuid.uuid4().hex[:12].upper()}"
        return {
            "provider": self.provider_code,
            "external_transaction_id": external_id,
            "amount": amount,
            "currency": currency,
            "status": PAYMENT_GATEWAY_COMPLETED,
            "metadata": metadata or {},
        }

    def verify_webhook(self, payload, headers=None):
        return {
            "provider": self.provider_code,
            "event_type": payload.get("event_type", "payment.updated"),
            "external_transaction_id": payload.get("external_transaction_id"),
            "status": payload.get("status", PAYMENT_GATEWAY_COMPLETED),
        }

    def process_refund(self, external_transaction_id, amount, reason=None):
        return {
            "provider": self.provider_code,
            "provider_refund_id": f"RF-{self.provider_code}-{uuid.uuid4().hex[:10].upper()}",
            "amount": amount,
            "status": PAYMENT_REFUND_COMPLETED,
            "reason": reason,
        }


class StripeProvider(BasePaymentProvider):

    provider_code = PAYMENT_PROVIDER_STRIPE


class VNPayProvider(BasePaymentProvider):

    provider_code = PAYMENT_PROVIDER_VNPAY


class MoMoProvider(BasePaymentProvider):

    provider_code = PAYMENT_PROVIDER_MOMO


class PaymentGatewayService:

    _providers = {
        PAYMENT_PROVIDER_STRIPE: StripeProvider(),
        PAYMENT_PROVIDER_VNPAY: VNPayProvider(),
        PAYMENT_PROVIDER_MOMO: MoMoProvider(),
    }

    @classmethod
    def get_provider(cls, provider_code):
        provider = cls._providers.get((provider_code or "").upper())
        if not provider:
            raise PaymentGatewayError(f"Unsupported payment provider: {provider_code}", 400)
        return provider

    @classmethod
    def supported_providers(cls):
        return list(cls._providers.keys())


class PaymentService:

    @staticmethod
    def _generate_payment_code():
        return f"PAY-GW-{Payment.query.count() + 1:06d}"

    @staticmethod
    def list_payments(invoice_id=None, provider=None):
        query = Payment.query
        if invoice_id:
            query = query.filter_by(invoice_id=invoice_id)
        if provider:
            query = query.filter_by(provider=provider.upper())
        rows = query.order_by(Payment.created_at.desc()).all()
        return {"count": len(rows), "payments": [row.to_dict() for row in rows]}

    @staticmethod
    def get_history(invoice_id=None, provider=None, limit=50):
        query = PaymentTransaction.query
        if provider:
            query = query.filter(PaymentTransaction.provider == provider.upper())
        if invoice_id:
            payment_ids = [row.id for row in Payment.query.filter_by(invoice_id=invoice_id).all()]
            if not payment_ids:
                return {"count": 0, "history": []}
            query = query.filter(PaymentTransaction.payment_id.in_(payment_ids))
        rows = query.order_by(PaymentTransaction.created_at.desc()).limit(limit).all()
        payload = []
        for row in rows:
            item = row.to_dict()
            item["payment"] = row.payment.to_dict() if row.payment else None
            payload.append(item)
        return {"count": len(payload), "history": payload}

    @staticmethod
    def create_payment(data, actor_email="SYSTEM", ip_address=""):
        invoice_id = data.get("invoice_id")
        provider_code = (data.get("provider") or PAYMENT_PROVIDER_VNPAY).upper()
        amount = data.get("amount")
        if not invoice_id:
            raise PaymentGatewayError("invoice_id is required", 400)

        invoice = Invoice.query.get(invoice_id)
        if not invoice:
            raise PaymentGatewayError("Invoice not found", 404)

        amount = float(amount if amount is not None else invoice.total_amount or 0)
        provider = PaymentGatewayService.get_provider(provider_code)
        provider_result = provider.create_payment(
            amount=amount,
            currency=data.get("currency", "VND"),
            metadata={"invoice_id": invoice_id, "invoice_no": invoice.invoice_no},
        )

        method = None
        if data.get("payment_method"):
            method = PaymentMethod(
                owner_type=data.get("owner_type", "INVOICE"),
                owner_id=invoice_id,
                method_type=data.get("method_type", "CARD"),
                provider=provider_code,
                display_name=data.get("display_name") or f"{provider_code} method",
                token_ref=data.get("token_ref"),
                last4=data.get("last4"),
                is_default=data.get("is_default", False),
            )
            db.session.add(method)
            db.session.flush()

        payment = Payment(
            invoice_id=invoice_id,
            amount=amount,
            payment_method=data.get("method_type") or data.get("payment_method") or provider_code,
            status=provider_result["status"],
            provider=provider_code,
            external_transaction_id=provider_result["external_transaction_id"],
            payment_method_id=method.id if method else None,
            metadata_json=json.dumps(provider_result.get("metadata") or {}),
            payment_date=datetime.utcnow(),
        )
        db.session.add(payment)
        db.session.flush()

        transaction = PaymentTransaction(
            payment_id=payment.id,
            provider=provider_code,
            external_transaction_id=provider_result["external_transaction_id"],
            amount=amount,
            currency=provider_result.get("currency", "VND"),
            status=provider_result["status"],
            raw_response_json=json.dumps(provider_result),
        )
        db.session.add(transaction)

        if provider_result["status"] == PAYMENT_GATEWAY_COMPLETED:
            invoice.payment_status = "PAID"

        write_audit("PAYMENT_GATEWAY_CREATE", "Payment", payment.id, actor_email, ip_address)
        db.session.commit()
        return {
            "payment": payment.to_dict(),
            "transaction": transaction.to_dict(),
            "provider": provider_code,
        }


class WebhookService:

    @staticmethod
    def process_webhook(provider_code, payload, headers=None, actor_email="SYSTEM", ip_address=""):
        provider = PaymentGatewayService.get_provider(provider_code)
        event = provider.verify_webhook(payload or {}, headers=headers or {})

        webhook = PaymentWebhook(
            provider=provider_code.upper(),
            event_type=event.get("event_type", "payment.updated"),
            payload_json=json.dumps(payload or {}),
            processed=False,
        )
        db.session.add(webhook)

        external_id = event.get("external_transaction_id")
        transaction = None
        if external_id:
            transaction = PaymentTransaction.query.filter_by(external_transaction_id=external_id).first()
        if transaction:
            transaction.status = event.get("status", PAYMENT_GATEWAY_COMPLETED)
            transaction.raw_response_json = json.dumps(event)
            if transaction.payment:
                transaction.payment.status = transaction.status
                invoice = Invoice.query.get(transaction.payment.invoice_id)
                if invoice and transaction.status == PAYMENT_GATEWAY_COMPLETED:
                    invoice.payment_status = "PAID"

        webhook.processed = True
        write_audit("PAYMENT_GATEWAY_WEBHOOK", "PaymentWebhook", webhook.id, actor_email, ip_address)
        db.session.commit()
        return {
            "webhook": webhook.to_dict(),
            "transaction": transaction.to_dict() if transaction else None,
        }


class RefundService:

    @staticmethod
    def _generate_refund_code():
        return f"PGW-RFD-{Refund.query.count() + 1:06d}"

    @staticmethod
    def process_refund(data, actor_email="SYSTEM", ip_address=""):
        payment_id = data.get("payment_id")
        if not payment_id:
            raise PaymentGatewayError("payment_id is required", 400)

        payment = Payment.query.get(payment_id)
        if not payment:
            raise PaymentGatewayError("Payment not found", 404)
        if payment.status == PAYMENT_GATEWAY_REFUNDED:
            raise PaymentGatewayError("Payment already refunded", 409)

        transaction = (
            PaymentTransaction.query.filter_by(payment_id=payment.id)
            .order_by(PaymentTransaction.created_at.desc())
            .first()
        )
        if not transaction:
            raise PaymentGatewayError("Payment transaction not found", 404)

        provider = PaymentGatewayService.get_provider(payment.provider or transaction.provider)
        amount = float(data.get("amount") if data.get("amount") is not None else payment.amount or 0)
        provider_result = provider.process_refund(
            transaction.external_transaction_id,
            amount=amount,
            reason=data.get("reason"),
        )

        refund = Refund(
            payment_id=payment.id,
            transaction_id=transaction.id,
            refund_code=RefundService._generate_refund_code(),
            provider=payment.provider or transaction.provider,
            provider_refund_id=provider_result.get("provider_refund_id"),
            amount=amount,
            reason=data.get("reason"),
            status=provider_result.get("status", PAYMENT_REFUND_COMPLETED),
            processed_at=datetime.utcnow(),
        )
        db.session.add(refund)

        payment.status = PAYMENT_GATEWAY_REFUNDED
        transaction.status = PAYMENT_GATEWAY_REFUNDED
        invoice = Invoice.query.get(payment.invoice_id)
        if invoice:
            invoice.payment_status = "REFUNDED"

        write_audit("PAYMENT_GATEWAY_REFUND", "Refund", refund.id, actor_email, ip_address)
        db.session.commit()
        return {"refund": refund.to_dict(), "payment": payment.to_dict()}

    @staticmethod
    def list_refunds(payment_id=None):
        query = Refund.query
        if payment_id:
            query = query.filter_by(payment_id=payment_id)
        rows = query.order_by(Refund.created_at.desc()).all()
        return {"count": len(rows), "refunds": [row.to_dict() for row in rows]}
