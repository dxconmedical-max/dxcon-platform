import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.extensions.db import db
from app.models.company import Company
from app.models.partner import Partner
from app.models.partner_service_mapping import PartnerServiceMapping
from app.services.billing_service import BillingService
from app.services.marketplace_booking import MarketplaceBookingService
from app.services.order_workflow_service import OrderWorkflowService
from app.services.scheduling import SchedulingService
from app.services.slot_generation import SlotGenerationService
from app.models.diagnostic_category import DiagnosticCategory
from app.models.diagnostic_service import DiagnosticService
from app.core.statuses import MAPPING_ACTIVE, PARTNER_ACTIVE


class PartnerPortalTestCase(unittest.TestCase):
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
        svc = DiagnosticService(service_code="TSH", name="TSH", category_id=cat.id, is_active=True)
        db.session.add(svc)
        self.partner = Partner(
            partner_code="PTR-PP-001",
            partner_type="LABORATORY",
            legal_name="Portal Lab",
            display_name="Portal Lab",
            status=PARTNER_ACTIVE,
            pickup_sla_minutes=60,
        )
        db.session.add(self.partner)
        db.session.flush()
        self.mapping = PartnerServiceMapping(
            partner_id=self.partner.id,
            diagnostic_service_id=svc.id,
            partner_service_code="PP-TSH",
            partner_service_name="TSH",
            price=150000,
            status=MAPPING_ACTIVE,
        )
        db.session.add(self.mapping)
        db.session.commit()
        SlotGenerationService.generate_partner_daily_slots(self.partner.id, days=2)

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def _order(self):
        slot = SchedulingService.list_available_slots(self.partner.id)[0]
        booking = MarketplaceBookingService.create_booking(
            {
                "partner_service_mapping_id": self.mapping.id,
                "patient_name": "Portal Patient",
                "patient_phone": "0909000111",
                "requested_date": slot.slot_date,
            }
        )
        order = OrderWorkflowService.create_from_booking(booking.id)
        BillingService.create_invoice_from_medical_order(order.id)
        return order

    def test_partner_portal_apis(self):
        order = self._order()
        pid = self.partner.id

        dash = self.client.get(f"/api/v1/partner-portal/dashboard?partner_id={pid}")
        self.assertEqual(dash.status_code, 200)
        self.assertGreaterEqual(dash.get_json()["orders_total"], 1)

        orders = self.client.get(f"/api/v1/partner-portal/orders?partner_id={pid}")
        self.assertEqual(orders.status_code, 200)

        upload = self.client.post(
            "/api/v1/partner-portal/results/upload",
            json={
                "partner_id": pid,
                "medical_order_id": order.id,
                "file_name": "result.pdf",
            },
        )
        self.assertEqual(upload.status_code, 201)

        revenue = self.client.get(f"/api/v1/partner-portal/revenue?partner_id={pid}")
        self.assertEqual(revenue.status_code, 200)

        sla = self.client.get(f"/api/v1/partner-portal/sla?partner_id={pid}")
        self.assertEqual(sla.status_code, 200)

    def test_partner_portal_web_routes(self):
        routes = {str(r) for r in self.app.url_map.iter_rules()}
        for route in [
            "/partner-portal",
            "/partner-portal/orders",
            "/partner-portal/results",
            "/partner-portal/revenue",
            "/partner-portal/sla",
        ]:
            self.assertIn(route, routes)


if __name__ == "__main__":
    unittest.main()
