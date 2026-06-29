import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.core.statuses import BILLING_INVOICE_PAID, MAPPING_ACTIVE, PARTNER_ACTIVE
from app.extensions.db import db
from app.models.billing_ledger import BillingLedger
from app.models.company import Company
from app.models.diagnostic_category import DiagnosticCategory
from app.models.diagnostic_service import DiagnosticService
from app.models.partner import Partner
from app.models.partner_service_mapping import PartnerServiceMapping
from app.models.tax_record import TaxRecord
from app.services.marketplace_booking import MarketplaceBookingService
from app.services.order_workflow_service import OrderWorkflowService
from app.services.scheduling import SchedulingService
from app.services.slot_generation import SlotGenerationService


class BillingInvoiceTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()

        db.session.add(Company(company_code="DX", company_name="DxCon", tax_code="01"))
        cat = DiagnosticCategory(category_code="BIO", name="Bio", is_active=True)
        db.session.add(cat)
        db.session.flush()
        svc = DiagnosticService(service_code="GLU", name="Glucose", category_id=cat.id, is_active=True)
        db.session.add(svc)
        self.partner = Partner(
            partner_code="PTR-BIL-INV-001",
            partner_type="LABORATORY",
            legal_name="Billing Invoice Lab",
            display_name="Billing Invoice Lab",
            status=PARTNER_ACTIVE,
        )
        db.session.add(self.partner)
        db.session.flush()
        self.mapping = PartnerServiceMapping(
            partner_id=self.partner.id,
            diagnostic_service_id=svc.id,
            partner_service_code="BIL-INV-GLU",
            partner_service_name="Glucose",
            price=250000,
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
                "patient_name": "Billing Invoice Patient",
                "patient_phone": "0908333444",
                "requested_date": slot.slot_date,
            }
        )
        return OrderWorkflowService.create_from_booking(booking.id)

    def test_billing_invoice_apis(self):
        order = self._medical_order()

        create = self.client.post(
            "/api/v1/billing/invoices",
            json={"medical_order_id": order.id},
        )
        self.assertEqual(create.status_code, 201)
        invoice_id = create.get_json()["invoice"]["id"]
        self.assertGreaterEqual(TaxRecord.query.filter_by(invoice_id=invoice_id).count(), 1)
        self.assertGreaterEqual(BillingLedger.query.count(), 1)

        detail = self.client.get(f"/api/v1/billing/invoices/{invoice_id}")
        self.assertEqual(detail.status_code, 200)

        listing = self.client.get("/api/v1/billing/invoices")
        self.assertEqual(listing.status_code, 200)
        self.assertGreaterEqual(listing.get_json()["count"], 1)

        mark_paid = self.client.post(
            f"/api/v1/billing/invoices/{invoice_id}/mark-paid",
            json={"transaction_ref": "BIL-INV-001"},
        )
        self.assertEqual(mark_paid.status_code, 200)
        self.assertEqual(mark_paid.get_json()["invoice"]["billing_status"], BILLING_INVOICE_PAID)

        ledger = self.client.get("/api/v1/billing/ledger")
        self.assertEqual(ledger.status_code, 200)
        self.assertGreaterEqual(ledger.get_json()["count"], 1)

        summary = self.client.get("/api/v1/billing/summary")
        self.assertEqual(summary.status_code, 200)
        self.assertGreaterEqual(summary.get_json()["invoices_paid"], 1)

    def test_billing_invoice_web_routes(self):
        routes = {str(r) for r in self.app.url_map.iter_rules()}
        for route in ["/billing", "/billing/invoices", "/billing/ledger"]:
            self.assertIn(route, routes)


if __name__ == "__main__":
    unittest.main()
