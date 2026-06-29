from app.extensions.db import db
from app.models.commission_ledger import CommissionLedger
from app.models.commission_rule import CommissionRule
from app.models.doctor_commission import DoctorCommission
from app.models.invoice import Invoice


class CommissionError(Exception):

    def __init__(self, message, status_code=400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class CommissionService:

    DEFAULT_RATES = {
        "PARTNER": 15.0,
        "COLLECTOR": 5.0,
        "DOCTOR": 3.0,
        "PLATFORM": 10.0,
    }

    @staticmethod
    def _generate_ledger_code():
        count = CommissionLedger.query.count()
        return f"CL-{count + 1:06d}"

    @staticmethod
    def get_rule(role_type, partner_id=None, partner_type=None):
        query = CommissionRule.query.filter_by(role_type=role_type, status="ACTIVE")
        if partner_id:
            rule = query.filter_by(partner_id=partner_id).first()
            if rule:
                return rule
        if partner_type:
            rule = query.filter_by(partner_type=partner_type).first()
            if rule:
                return rule
        return query.first()

    @staticmethod
    def ensure_default_rules():
        created = 0
        defaults = [
            ("PARTNER_DEFAULT", "PARTNER", 15.0),
            ("COLLECTOR_DEFAULT", "COLLECTOR", 5.0),
            ("DOCTOR_DEFAULT", "DOCTOR", 3.0),
            ("PLATFORM_DEFAULT", "PLATFORM", 10.0),
        ]
        for code, role, rate in defaults:
            if not CommissionRule.query.filter_by(rule_code=code).first():
                db.session.add(
                    CommissionRule(
                        rule_code=code,
                        role_type=role,
                        rate_percent=rate,
                        status="ACTIVE",
                    )
                )
                created += 1
        if created:
            db.session.commit()
        return created

    @staticmethod
    def _calc_amount(gross, role_type, partner_id=None):
        rule = CommissionService.get_rule(role_type, partner_id=partner_id)
        rate = rule.rate_percent if rule else CommissionService.DEFAULT_RATES.get(role_type, 0)
        flat = rule.flat_fee if rule else 0
        return round((gross * rate / 100.0) + flat, 2), rule

    @staticmethod
    def calculate_for_invoice(
        invoice_id,
        partner_id=None,
        collector_id=None,
        doctor_id=None,
    ):
        invoice = Invoice.query.get(invoice_id)
        if not invoice:
            raise CommissionError("Invoice not found", 404)

        CommissionService.ensure_default_rules()
        gross = invoice.total_amount or 0
        entries = []

        for role_type, pid, cid, did in [
            ("PARTNER", partner_id or invoice.partner_id, None, None),
            ("COLLECTOR", None, collector_id, None),
            ("DOCTOR", None, None, doctor_id),
            ("PLATFORM", None, None, None),
        ]:
            amount, rule = CommissionService._calc_amount(
                gross,
                role_type,
                partner_id=pid if role_type == "PARTNER" else None,
            )
            if amount <= 0:
                continue

            existing = CommissionLedger.query.filter_by(
                invoice_id=invoice.id,
                role_type=role_type,
            ).first()
            if existing:
                entries.append(existing)
                continue

            entry = CommissionLedger(
                ledger_code=CommissionService._generate_ledger_code(),
                medical_order_id=invoice.medical_order_id,
                invoice_id=invoice.id,
                partner_id=pid,
                collector_id=cid,
                doctor_id=did,
                role_type=role_type,
                gross_amount=gross,
                commission_amount=amount,
                rule_id=rule.id if rule else None,
            )
            db.session.add(entry)
            entries.append(entry)

            if role_type == "DOCTOR" and doctor_id:
                db.session.add(
                    DoctorCommission(
                        commission_code=f"DC-{entry.ledger_code}",
                        doctor_id=doctor_id,
                        medical_order_id=invoice.medical_order_id,
                        invoice_id=invoice.id,
                        amount=amount,
                        status="PENDING",
                    )
                )

        db.session.commit()
        return entries

    @staticmethod
    def list_commissions(partner_id=None, invoice_id=None):
        query = CommissionLedger.query
        if partner_id:
            query = query.filter_by(partner_id=partner_id)
        if invoice_id:
            query = query.filter_by(invoice_id=invoice_id)
        return query.order_by(CommissionLedger.created_at.desc()).all()

    @staticmethod
    def list_rules():
        return CommissionRule.query.order_by(CommissionRule.created_at.desc()).all()
