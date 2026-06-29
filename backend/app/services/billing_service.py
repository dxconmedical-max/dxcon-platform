from datetime import datetime

from app.core.audit import write_audit
from app.core.events import write_event
from app.core.statuses import (
    BILLING_ACCOUNT_ACTIVE,
    BILLING_ADJUSTMENT_APPLIED,
    BILLING_INVOICE_ISSUED,
    BILLING_INVOICE_PAID,
    BILLING_LEDGER_CREDIT,
    BILLING_LEDGER_DEBIT,
    PAYMENT_RECORD_COMPLETED,
    TAX_RECORD_APPLIED,
)
from app.extensions.db import db
from app.models.company import Company
from app.models.invoice import Invoice
from app.models.invoice_item import InvoiceItem
from app.models.billing_account import BillingAccount
from app.models.billing_ledger import BillingLedger
from app.models.billing_adjustment import BillingAdjustment
from app.models.tax_record import TaxRecord
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

    @staticmethod
    def get_summary(partner_id=None):
        query = Invoice.query.filter(Invoice.medical_order_id.isnot(None))
        if partner_id:
            query = query.filter_by(partner_id=partner_id)
        invoices = query.all()
        paid = [inv for inv in invoices if inv.billing_status == BILLING_INVOICE_PAID]
        issued = [inv for inv in invoices if inv.billing_status == BILLING_INVOICE_ISSUED]
        ledger = BillingLedger.query.order_by(BillingLedger.created_at.desc()).limit(20).all()
        taxes = TaxRecord.query.order_by(TaxRecord.created_at.desc()).limit(20).all()
        adjustments = BillingAdjustment.query.order_by(BillingAdjustment.created_at.desc()).limit(20).all()

        return {
            "invoices_total": len(invoices),
            "invoices_paid": len(paid),
            "invoices_outstanding": len(issued),
            "revenue_total": sum(inv.total_amount or 0 for inv in paid),
            "outstanding_total": sum(inv.total_amount or 0 for inv in issued),
            "tax_total": sum(row.tax_amount or 0 for row in taxes),
            "adjustments_total": sum(
                row.amount or 0 for row in adjustments if row.status == BILLING_ADJUSTMENT_APPLIED
            ),
            "recent_ledger": [row.to_dict() for row in ledger],
        }


class LedgerService:

    @staticmethod
    def _generate_account_code(owner_type, owner_id):
        return f"ACC-{owner_type[:3]}-{owner_id[:8]}"

    @staticmethod
    def ensure_account(owner_type, owner_id, currency="VND"):
        account = BillingAccount.query.filter_by(owner_type=owner_type, owner_id=owner_id).first()
        if account:
            return account
        account = BillingAccount(
            account_code=LedgerService._generate_account_code(owner_type, owner_id),
            owner_type=owner_type,
            owner_id=owner_id,
            currency=currency,
            status=BILLING_ACCOUNT_ACTIVE,
        )
        db.session.add(account)
        db.session.flush()
        return account

    @staticmethod
    def record_entry(account_id, entry_type, amount, reference_type=None, reference_id=None, description=None):
        account = BillingAccount.query.get(account_id)
        if not account:
            raise BillingError("Billing account not found", 404)

        entry = BillingLedger(
            account_id=account_id,
            entry_type=entry_type,
            amount=amount,
            reference_type=reference_type,
            reference_id=reference_id,
            description=description,
        )
        db.session.add(entry)
        if entry_type == BILLING_LEDGER_DEBIT:
            account.balance = (account.balance or 0) + amount
        else:
            account.balance = (account.balance or 0) - amount
        db.session.flush()
        return entry

    @staticmethod
    def record_invoice_entries(invoice):
        company_account = LedgerService.ensure_account("COMPANY", invoice.company_id)
        LedgerService.record_entry(
            company_account.id,
            BILLING_LEDGER_DEBIT,
            invoice.total_amount or 0,
            reference_type="Invoice",
            reference_id=invoice.id,
            description=f"Invoice {invoice.invoice_no} issued",
        )
        if invoice.partner_id:
            partner_account = LedgerService.ensure_account("PARTNER", invoice.partner_id)
            LedgerService.record_entry(
                partner_account.id,
                BILLING_LEDGER_CREDIT,
                invoice.total_amount or 0,
                reference_type="Invoice",
                reference_id=invoice.id,
                description=f"Invoice {invoice.invoice_no} receivable",
            )

    @staticmethod
    def record_payment_entry(invoice, payment):
        company_account = LedgerService.ensure_account("COMPANY", invoice.company_id)
        LedgerService.record_entry(
            company_account.id,
            BILLING_LEDGER_CREDIT,
            payment.amount or 0,
            reference_type="PaymentRecord",
            reference_id=payment.id,
            description=f"Payment {payment.payment_code} for invoice {invoice.invoice_no}",
        )

    @staticmethod
    def list_ledger(account_id=None, reference_id=None, limit=100):
        query = BillingLedger.query
        if account_id:
            query = query.filter_by(account_id=account_id)
        if reference_id:
            query = query.filter_by(reference_id=reference_id)
        rows = query.order_by(BillingLedger.created_at.desc()).limit(limit).all()
        return {"count": len(rows), "entries": [row.to_dict() for row in rows]}


class TaxService:

    @staticmethod
    def apply_tax(invoice_id, tax_code="VAT", tax_rate=0.1):
        invoice = Invoice.query.get(invoice_id)
        if not invoice:
            raise BillingError("Invoice not found", 404)

        existing = TaxRecord.query.filter_by(invoice_id=invoice_id, status=TAX_RECORD_APPLIED).first()
        if existing:
            return existing

        tax_amount = round((invoice.total_amount or 0) * tax_rate, 2)
        record = TaxRecord(
            invoice_id=invoice_id,
            tax_code=tax_code,
            tax_rate=tax_rate,
            tax_amount=tax_amount,
            status=TAX_RECORD_APPLIED,
        )
        db.session.add(record)
        db.session.flush()
        return record

    @staticmethod
    def list_tax_records(invoice_id=None):
        query = TaxRecord.query
        if invoice_id:
            query = query.filter_by(invoice_id=invoice_id)
        rows = query.order_by(TaxRecord.created_at.desc()).all()
        return {"count": len(rows), "tax_records": [row.to_dict() for row in rows]}


class InvoiceService:

    @staticmethod
    def list_invoices(partner_id=None, status=None):
        invoices = BillingService.list_invoices(partner_id=partner_id, status=status)
        return {"count": len(invoices), "invoices": [inv.to_dict() for inv in invoices]}

    @staticmethod
    def create_invoice(medical_order_id, actor_email="SYSTEM", ip_address=""):
        invoice = BillingService.create_invoice_from_medical_order(
            medical_order_id,
            actor_email=actor_email,
            ip_address=ip_address,
        )
        if not TaxRecord.query.filter_by(invoice_id=invoice.id, status=TAX_RECORD_APPLIED).first():
            TaxService.apply_tax(invoice.id)
        if not BillingLedger.query.filter_by(reference_id=invoice.id, reference_type="Invoice").first():
            LedgerService.record_invoice_entries(invoice)
        db.session.commit()
        return invoice

    @staticmethod
    def get_invoice(invoice_id):
        return BillingService.get_invoice_detail(invoice_id)

    @staticmethod
    def mark_paid(invoice_id, amount=None, payment_method="BANK_TRANSFER", transaction_ref=None, actor_email="SYSTEM", ip_address=""):
        invoice = Invoice.query.get(invoice_id)
        if not invoice:
            raise BillingError("Invoice not found", 404)
        if invoice.billing_status == BILLING_INVOICE_PAID:
            raise BillingError("Invoice is already paid", 400)

        payment, invoice = BillingService.record_payment(
            invoice_id,
            amount=amount,
            payment_method=payment_method,
            transaction_ref=transaction_ref,
            actor_email=actor_email,
            ip_address=ip_address,
        )
        LedgerService.record_payment_entry(invoice, payment)
        db.session.commit()
        return {"invoice": invoice.to_dict(), "payment": payment.to_dict()}
