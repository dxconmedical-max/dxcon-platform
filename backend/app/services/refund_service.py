from datetime import datetime

from app.core.audit import write_audit
from app.core.events import write_event
from app.core.statuses import (
    BILLING_INVOICE_REFUNDED,
    PAYMENT_RECORD_REFUNDED,
    REFUND_COMPLETED,
)
from app.extensions.db import db
from app.models.invoice import Invoice
from app.models.payment_record import PaymentRecord
from app.models.refund_record import RefundRecord
from app.services.order_workflow_service import OrderWorkflowService


class RefundServiceError(Exception):

    def __init__(self, message, status_code=400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class RefundService:

    @staticmethod
    def _generate_refund_code():
        count = RefundRecord.query.count()
        return f"RFD-{count + 1:06d}"

    @staticmethod
    def process_refund(
        invoice_id,
        reason=None,
        amount=None,
        actor_email="SYSTEM",
        ip_address="",
    ):
        invoice = Invoice.query.get(invoice_id)
        if not invoice:
            raise RefundServiceError("Invoice not found", 404)

        if invoice.billing_status == BILLING_INVOICE_REFUNDED:
            raise RefundServiceError("Invoice already refunded", 409)

        payment = PaymentRecord.query.filter_by(
            invoice_id=invoice.id,
            status="COMPLETED",
        ).order_by(PaymentRecord.created_at.desc()).first()

        refund_amount = float(amount if amount is not None else invoice.total_amount or 0)
        refund = RefundRecord(
            refund_code=RefundService._generate_refund_code(),
            invoice_id=invoice.id,
            medical_order_id=invoice.medical_order_id,
            payment_record_id=payment.id if payment else None,
            amount=refund_amount,
            reason=reason,
            status=REFUND_COMPLETED,
            processed_at=datetime.utcnow(),
        )
        db.session.add(refund)

        invoice.billing_status = BILLING_INVOICE_REFUNDED
        invoice.payment_status = "REFUNDED"

        if payment:
            payment.status = PAYMENT_RECORD_REFUNDED

        if invoice.medical_order_id:
            try:
                OrderWorkflowService.refund_order(
                    invoice.medical_order_id,
                    reason=reason,
                    actor_email=actor_email,
                    ip_address=ip_address,
                )
            except Exception:
                pass

        write_audit(
            action="BILLING_REFUND_PROCESSED",
            object_type="RefundRecord",
            object_id=refund.id,
            user_email=actor_email,
            ip_address=ip_address,
        )
        write_event(
            event_type="BILLING_REFUND_PROCESSED",
            object_type="RefundRecord",
            object_id=refund.id,
            message=f"Refund {refund.refund_code} processed for invoice {invoice.invoice_no}",
        )
        db.session.commit()
        return refund, invoice

    @staticmethod
    def list_refunds(invoice_id=None):
        query = RefundRecord.query
        if invoice_id:
            query = query.filter_by(invoice_id=invoice_id)
        return query.order_by(RefundRecord.created_at.desc()).all()
