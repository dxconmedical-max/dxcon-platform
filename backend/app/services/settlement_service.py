from datetime import datetime

from app.core.audit import write_audit
from app.core.events import write_event
from app.core.statuses import SETTLEMENT_PAID, SETTLEMENT_PENDING
from app.extensions.db import db
from app.models.commission_ledger import CommissionLedger
from app.models.invoice import Invoice
from app.models.partner_settlement import PartnerSettlement
from app.models.settlement_item import SettlementItem
from app.models.collector_payout import CollectorPayout
from app.services.commission_service import CommissionService


class SettlementError(Exception):

    def __init__(self, message, status_code=400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class SettlementService:

    @staticmethod
    def _generate_settlement_code():
        count = PartnerSettlement.query.count()
        return f"STL-{count + 1:06d}"

    @staticmethod
    def create_settlement(partner_id, period_start=None, period_end=None, actor_email="SYSTEM", ip_address=""):
        invoices = Invoice.query.filter_by(
            partner_id=partner_id,
            billing_status="PAID",
        ).all()

        if not invoices:
            raise SettlementError("No paid invoices available for settlement", 409)

        settlement = PartnerSettlement(
            settlement_code=SettlementService._generate_settlement_code(),
            partner_id=partner_id,
            period_start=period_start,
            period_end=period_end,
            status=SETTLEMENT_PENDING,
        )
        db.session.add(settlement)
        db.session.flush()

        gross = 0.0
        commission = 0.0
        for invoice in invoices:
            ledger_entries = CommissionLedger.query.filter_by(
                invoice_id=invoice.id,
                partner_id=partner_id,
            ).all()
            item_commission = sum(entry.commission_amount for entry in ledger_entries)
            item_gross = invoice.total_amount or 0
            item_net = item_gross - item_commission

            db.session.add(
                SettlementItem(
                    settlement_id=settlement.id,
                    invoice_id=invoice.id,
                    medical_order_id=invoice.medical_order_id,
                    description=f"Invoice {invoice.invoice_no}",
                    gross_amount=item_gross,
                    commission_amount=item_commission,
                    net_amount=item_net,
                )
            )
            gross += item_gross
            commission += item_commission

        settlement.gross_amount = gross
        settlement.commission_amount = commission
        settlement.net_amount = gross - commission

        write_audit(
            action="PARTNER_SETTLEMENT_CREATED",
            object_type="PartnerSettlement",
            object_id=settlement.id,
            user_email=actor_email,
            ip_address=ip_address,
        )
        write_event(
            event_type="PARTNER_SETTLEMENT_CREATED",
            object_type="PartnerSettlement",
            object_id=settlement.id,
            message=f"Settlement {settlement.settlement_code} created",
        )
        db.session.commit()
        return settlement

    @staticmethod
    def finalize_settlement(settlement_id, actor_email="SYSTEM", ip_address=""):
        settlement = PartnerSettlement.query.get(settlement_id)
        if not settlement:
            raise SettlementError("Settlement not found", 404)

        settlement.status = SETTLEMENT_PAID
        settlement.paid_at = datetime.utcnow()
        settlement.updated_at = datetime.utcnow()

        collector_entries = CommissionLedger.query.filter_by(
            partner_id=settlement.partner_id,
            role_type="COLLECTOR",
        ).all()
        for index, entry in enumerate(collector_entries, start=1):
            if entry.collector_id:
                db.session.add(
                    CollectorPayout(
                        payout_code=f"PO-{settlement.settlement_code}-{index:03d}",
                        collector_id=entry.collector_id,
                        settlement_id=settlement.id,
                        amount=entry.commission_amount,
                        status="PAID",
                        paid_at=datetime.utcnow(),
                    )
                )

        write_audit(
            action="PARTNER_SETTLEMENT_PAID",
            object_type="PartnerSettlement",
            object_id=settlement.id,
            user_email=actor_email,
            ip_address=ip_address,
        )
        db.session.commit()
        return settlement

    @staticmethod
    def list_settlements(partner_id=None):
        query = PartnerSettlement.query
        if partner_id:
            query = query.filter_by(partner_id=partner_id)
        return query.order_by(PartnerSettlement.created_at.desc()).all()

    @staticmethod
    def get_settlement_detail(settlement_id):
        settlement = PartnerSettlement.query.get(settlement_id)
        if not settlement:
            raise SettlementError("Settlement not found", 404)
        items = SettlementItem.query.filter_by(settlement_id=settlement.id).all()
        payouts = CollectorPayout.query.filter_by(settlement_id=settlement.id).all()
        payload = settlement.to_dict()
        payload["items"] = [item.to_dict() for item in items]
        payload["collector_payouts"] = [payout.to_dict() for payout in payouts]
        return payload

    @staticmethod
    def build_settlement_with_commissions(invoice_id, partner_id, collector_id=None, doctor_id=None):
        CommissionService.calculate_for_invoice(
            invoice_id,
            partner_id=partner_id,
            collector_id=collector_id,
            doctor_id=doctor_id,
        )
        return SettlementService.create_settlement(partner_id)
