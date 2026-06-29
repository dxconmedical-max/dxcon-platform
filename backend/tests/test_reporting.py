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
from app.models.kpi_event import KPIEvent
from app.models.partner import Partner
from app.models.partner_service_mapping import PartnerServiceMapping
from app.models.report_snapshot import ReportSnapshot
from app.services.billing_service import BillingService
from app.services.marketplace_booking import MarketplaceBookingService
from app.services.order_workflow_service import OrderWorkflowService
from app.services.reporting_service import ExecutiveDashboardService, KPIService, ReportingService
from app.services.scheduling import SchedulingService
from app.services.slot_generation import SlotGenerationService
from app.models.diagnostic_category import DiagnosticCategory
from app.models.diagnostic_service import DiagnosticService
from app.core.statuses import MAPPING_ACTIVE, PARTNER_ACTIVE


class ReportingTestCase(unittest.TestCase):
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
            partner_code="PTR-RPT-001",
            partner_type="LABORATORY",
            legal_name="Report Lab",
            display_name="Report Lab",
            status=PARTNER_ACTIVE,
            pickup_sla_minutes=60,
        )
        db.session.add(self.partner)
        db.session.flush()
        self.mapping = PartnerServiceMapping(
            partner_id=self.partner.id,
            diagnostic_service_id=svc.id,
            partner_service_code="RPT-TSH",
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

    def _seed_order(self):
        slot = SchedulingService.list_available_slots(self.partner.id)[0]
        booking = MarketplaceBookingService.create_booking(
            {
                "partner_service_mapping_id": self.mapping.id,
                "patient_name": "Report Patient",
                "patient_phone": "0909000222",
                "requested_date": slot.slot_date,
            }
        )
        order = OrderWorkflowService.create_from_booking(booking.id)
        BillingService.create_invoice_from_medical_order(order.id)
        return order

    def test_reporting_apis(self):
        self._seed_order()

        kpi = self.client.get("/api/v1/reports/kpi")
        self.assertEqual(kpi.status_code, 200)
        self.assertGreaterEqual(kpi.get_json()["orders_total"], 1)

        revenue = self.client.get("/api/v1/reports/revenue")
        self.assertEqual(revenue.status_code, 200)

        operations = self.client.get("/api/v1/reports/operations")
        self.assertEqual(operations.status_code, 200)
        ops = operations.get_json()
        self.assertIn("daily_bookings", ops)
        self.assertIn("order_status_distribution", ops)

        partners = self.client.get("/api/v1/reports/partners")
        self.assertEqual(partners.status_code, 200)
        self.assertGreaterEqual(partners.get_json()["partners_total"], 1)

        collectors = self.client.get("/api/v1/reports/collectors")
        self.assertEqual(collectors.status_code, 200)

    def test_reporting_services_and_models(self):
        self._seed_order()
        summary = KPIService.get_kpi_summary()
        self.assertGreaterEqual(summary["orders_total"], 1)

        dashboard = ExecutiveDashboardService.get_dashboard()
        self.assertIn("kpi", dashboard)
        self.assertIn("revenue", dashboard)

        snapshot = ReportingService.save_snapshot("KPI", summary)
        self.assertIsNotNone(ReportSnapshot.query.get(snapshot.id))

        event = KPIService.record_event("TEST_KPI", 1.0, dimension="TEST")
        self.assertIsNotNone(KPIEvent.query.get(event.id))

    def test_reporting_web_routes(self):
        routes = {str(r) for r in self.app.url_map.iter_rules()}
        for route in ["/reports", "/reports/executive", "/reports/operations"]:
            self.assertIn(route, routes)


if __name__ == "__main__":
    unittest.main()
