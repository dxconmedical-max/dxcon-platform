from datetime import datetime

from app.core.audit import write_audit
from app.core.events import write_event
from app.core.statuses import (
    BILLING_INVOICE_ISSUED,
    BILLING_INVOICE_PAID,
    PAYMENT_RECORD_COMPLETED,
)
from app.extensions.db import db
from app.models.company import Company
from app.models.invoice import Invoice
from app.models.invoice_item import InvoiceItem
from app.models.medical_order import MedicalOrder
from app.models.payment_record import PaymentRecord


class BillingError(Exception):

    def __init__(self, message, status_code=400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class BillingService:

    @staticmethod
    def _generate_invoice_no():
        count = Invoice.query.count()
        return f"INV-{count + 1:06d}"

    @staticmethod
    def _generate_payment_code():
        count = PaymentRecord.query.count()
        return f"PAY-{count + 1:06d}"

    @staticmethod
    def create_invoice_from_medical_order(
        medical_order_id,
        actor_email="SYSTEM",
        ip_address="",
    ):
        order = MedicalOrder.query.get(medical_order_id)
        if not order:
            raise BillingError("Medical order not found", 404)

        existing = Invoice.query.filter_by(medical_order_id=medical_order_id).first()
        if existing:
            return existing

        company = Company.query.first()
        if not company:
            raise BillingError("Company not found for billing", 404)

        invoice = Invoice(
            invoice_no=BillingService._generate_invoice_no(),
            company_id=company.id,
            order_id=order.legacy_order_id or order.id,
            medical_order_id=order.id,
            partner_id=order.partner_id,
            total_amount=order.total_amount or 0,
            payment_status="UNPAID",
            billing_status=BILLING_INVOICE_ISSUED,
        )
        db.session.add(invoice)
        db.session.flush()

        db.session.add(
            InvoiceItem(
                invoice_id=invoice.id,
                description=f"Medical order {order.order_code}",
                service_code=order.diagnostic_service_id,
                quantity=1,
                unit_price=order.total_amount or 0,
                line_total=order.total_amount or 0,
            )
        )

        write_audit(
            action="BILLING_INVOICE_CREATED",
            object_type="Invoice",
            object_id=invoice.id,
            user_email=actor_email,
            ip_address=ip_address,
        )
        write_event(
            event_type="BILLING_INVOICE_CREATED",
            object_type="Invoice",
            object_id=invoice.id,
            message=f"Invoice {invoice.invoice_no} created for order {order.order_code}",
        )
        db.session.commit()
        return invoice

    @staticmethod
    def list_invoices(partner_id=None, status=None):
        query = Invoice.query.filter(Invoice.medical_order_id.isnot(None))
        if partner_id:
            query = query.filter_by(partner_id=partner_id)
        if status:
            query = query.filter_by(billing_status=status)
        return query.order_by(Invoice.created_at.desc()).all()

    @staticmethod
    def get_invoice_detail(invoice_id):
        invoice = Invoice.query.get(invoice_id)
        if not invoice:
            raise BillingError("Invoice not found", 404)
        items = InvoiceItem.query.filter_by(invoice_id=invoice.id).all()
        payments = PaymentRecord.query.filter_by(invoice_id=invoice.id).all()
        payload = invoice.to_dict()
        payload["items"] = [item.to_dict() for item in items]
        payload["payments"] = [payment.to_dict() for payment in payments]
        return payload

    @staticmethod
    def record_payment(
        invoice_id,
        amount=None,
        payment_method="BANK_TRANSFER",
        transaction_ref=None,
        actor_email="SYSTEM",
        ip_address="",
    ):
        invoice = Invoice.query.get(invoice_id)
        if not invoice:
            raise BillingError("Invoice not found", 404)

        pay_amount = float(amount if amount is not None else invoice.total_amount)
        payment = PaymentRecord(
            invoice_id=invoice.id,
            payment_code=BillingService._generate_payment_code(),
            amount=pay_amount,
            payment_method=payment_method,
            status=PAYMENT_RECORD_COMPLETED,
            transaction_ref=transaction_ref,
            paid_at=datetime.utcnow(),
        )
        db.session.add(payment)

        invoice.payment_status = "PAID"
        invoice.billing_status = BILLING_INVOICE_PAID

        write_audit(
            action="BILLING_PAYMENT_RECORDED",
            object_type="PaymentRecord",
            object_id=payment.id,
            user_email=actor_email,
            ip_address=ip_address,
        )
        write_event(
            event_type="BILLING_PAYMENT_RECORDED",
            object_type="PaymentRecord",
            object_id=payment.id,
            message=f"Payment {payment.payment_code} recorded for invoice {invoice.invoice_no}",
        )
        db.session.commit()
        return payment, invoice

    @staticmethod
    def list_payments(invoice_id=None):
        query = PaymentRecord.query
        if invoice_id:
            query = query.filter_by(invoice_id=invoice_id)
        return query.order_by(PaymentRecord.created_at.desc()).all()
