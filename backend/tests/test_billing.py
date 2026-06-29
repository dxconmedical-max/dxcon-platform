import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.core.statuses import BILLING_INVOICE_PAID, SETTLEMENT_PAID
from app.extensions.db import db
from app.models.commission_ledger import CommissionLedger
from app.models.company import Company
from app.models.invoice import Invoice
from app.models.payment_record import PaymentRecord
from app.models.refund_record import RefundRecord
from app.services.billing_service import BillingService
from app.services.commission_service import CommissionService
from app.services.order_workflow_service import OrderWorkflowService
from app.services.refund_service import RefundService
from app.services.settlement_service import SettlementService
from app.models.diagnostic_category import DiagnosticCategory
from app.models.diagnostic_service import DiagnosticService
from app.models.partner import Partner
from app.models.partner_service_mapping import PartnerServiceMapping
from app.services.marketplace_booking import MarketplaceBookingService
from app.services.scheduling import SchedulingService
from app.services.slot_generation import SlotGenerationService
from app.core.statuses import MAPPING_ACTIVE, PARTNER_ACTIVE


class BillingTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()

        self.company = Company(
            company_code="DXCON",
            company_name="DxCon Platform",
            tax_code="0100000000",
        )
        db.session.add(self.company)

        category = DiagnosticCategory(category_code="BIO", name="Bio", is_active=True)
        db.session.add(category)
        db.session.flush()

        service = DiagnosticService(
            service_code="GLU",
            name="Glucose",
            category_id=category.id,
            is_active=True,
        )
        db.session.add(service)

        self.partner = Partner(
            partner_code="PTR-BIL-001",
            partner_type="LABORATORY",
            legal_name="Billing Lab",
            display_name="Billing Lab",
            status=PARTNER_ACTIVE,
        )
        db.session.add(self.partner)
        db.session.flush()

        self.mapping = PartnerServiceMapping(
            partner_id=self.partner.id,
            diagnostic_service_id=service.id,
            partner_service_code="BIL-GLU",
            partner_service_name="Glucose",
            price=200000,
            status=MAPPING_ACTIVE,
        )
        db.session.add(self.mapping)
        db.session.commit()

        SlotGenerationService.generate_partner_daily_slots(self.partner.id, days=2)

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def _medical_order(self):
        slot = SchedulingService.list_available_slots(self.partner.id)[0]
        booking = MarketplaceBookingService.create_booking(
            {
                "partner_service_mapping_id": self.mapping.id,
                "patient_name": "Billing Patient",
                "patient_phone": "0908111222",
                "requested_date": slot.slot_date,
            }
        )
        return OrderWorkflowService.create_from_booking(booking.id)

    def test_invoice_and_payment_flow(self):
        order = self._medical_order()
        response = self.client.post(
            "/api/v1/billing/invoices",
            json={"medical_order_id": order.id},
        )
        self.assertEqual(response.status_code, 201)
        invoice_id = response.get_json()["invoice"]["id"]

        payment = self.client.post(
            "/api/v1/billing/payments",
            json={"invoice_id": invoice_id, "transaction_ref": "TXN-001"},
        )
        self.assertEqual(payment.status_code, 201)
        self.assertEqual(payment.get_json()["invoice"]["billing_status"], BILLING_INVOICE_PAID)

    def test_commission_settlement_and_refund(self):
        order = self._medical_order()
        invoice = BillingService.create_invoice_from_medical_order(order.id)
        BillingService.record_payment(invoice.id)

        calc = self.client.post(
            "/api/v1/billing/commissions/calculate",
            json={"invoice_id": invoice.id, "partner_id": self.partner.id},
        )
        self.assertEqual(calc.status_code, 200)
        self.assertGreater(CommissionLedger.query.count(), 0)

        settlement = self.client.post(
            "/api/v1/billing/settlements",
            json={"partner_id": self.partner.id},
        )
        self.assertEqual(settlement.status_code, 201)
        settlement_id = settlement.get_json()["settlement"]["id"]

        finalize = self.client.post(
            f"/api/v1/billing/settlements/{settlement_id}/finalize"
        )
        self.assertEqual(finalize.status_code, 200)
        self.assertEqual(finalize.get_json()["settlement"]["status"], SETTLEMENT_PAID)

        refund = self.client.post(
            "/api/v1/billing/refunds",
            json={"invoice_id": invoice.id, "reason": "Patient cancellation"},
        )
        self.assertEqual(refund.status_code, 201)
        self.assertEqual(RefundRecord.query.count(), 1)

    def test_billing_routes_registered(self):
        routes = {str(rule) for rule in self.app.url_map.iter_rules()}
        for route in [
            "/api/v1/billing/invoices",
            "/api/v1/billing/payments",
            "/api/v1/billing/refunds",
            "/api/v1/billing/settlements",
            "/api/v1/billing/commissions",
        ]:
            self.assertIn(route, routes)


if __name__ == "__main__":
    unittest.main()
