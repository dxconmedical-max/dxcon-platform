import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.core.statuses import MAPPING_ACTIVE, PARTNER_ACTIVE
from app.extensions.db import db
from app.models.clinic_profile import ClinicProfile
from app.models.clinic_revenue_summary import ClinicRevenueSummary
from app.models.company import Company
from app.models.diagnostic_category import DiagnosticCategory
from app.models.diagnostic_service import DiagnosticService
from app.models.partner import Partner
from app.models.partner_service_mapping import PartnerServiceMapping
from app.services.slot_generation import SlotGenerationService
from scripts.seed_clinic_portal_demo import seed_clinic_portal_demo, seed_clinic_portal_flow


class ClinicPortalTestCase(unittest.TestCase):
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
            partner_code="PTR-CLN-001",
            partner_type="CLINIC",
            legal_name="Clinic Portal Lab",
            display_name="Clinic Portal Lab",
            status=PARTNER_ACTIVE,
        )
        db.session.add(self.partner)
        db.session.flush()
        self.mapping = PartnerServiceMapping(
            partner_id=self.partner.id,
            diagnostic_service_id=svc.id,
            partner_service_code="CLN-GLU",
            partner_service_name="Glucose",
            price=120000,
            status=MAPPING_ACTIVE,
        )
        db.session.add(self.mapping)
        db.session.commit()
        SlotGenerationService.generate_partner_daily_slots(self.partner.id, days=2)
        seed_clinic_portal_demo(partner=self.partner)
        self.flow = seed_clinic_portal_flow(partner=self.partner, mapping=self.mapping)
        self.clinic_id = self.flow["clinic_id"]
        self.patient_id = self.flow["patient_id"]

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def test_clinic_portal_apis(self):
        cid = self.clinic_id

        dashboard = self.client.get(f"/api/v1/clinic/dashboard?clinic_id={cid}")
        self.assertEqual(dashboard.status_code, 200)
        self.assertGreaterEqual(dashboard.get_json()["summary"]["patients_total"], 1)

        profile = self.client.get(f"/api/v1/clinic/profile?clinic_id={cid}")
        self.assertEqual(profile.status_code, 200)

        update = self.client.put(
            f"/api/v1/clinic/profile?clinic_id={cid}",
            json={"address": "Updated clinic address"},
        )
        self.assertEqual(update.status_code, 200)

        bookings = self.client.get(f"/api/v1/clinic/bookings?clinic_id={cid}")
        self.assertEqual(bookings.status_code, 200)
        self.assertGreaterEqual(bookings.get_json()["count"], 1)

        orders = self.client.get(f"/api/v1/clinic/orders?clinic_id={cid}")
        self.assertEqual(orders.status_code, 200)
        self.assertGreaterEqual(orders.get_json()["count"], 1)

        patients = self.client.get(f"/api/v1/clinic/patients?clinic_id={cid}")
        self.assertEqual(patients.status_code, 200)
        self.assertGreaterEqual(patients.get_json()["count"], 1)

        doctors = self.client.get(f"/api/v1/clinic/doctors?clinic_id={cid}")
        self.assertEqual(doctors.status_code, 200)
        self.assertGreaterEqual(doctors.get_json()["count"], 1)

        revenue = self.client.get(f"/api/v1/clinic/revenue?clinic_id={cid}")
        self.assertEqual(revenue.status_code, 200)

    def test_clinic_portal_services(self):
        profile = ClinicProfile.query.filter_by(clinic_id=self.clinic_id).first()
        self.assertIsNotNone(profile)
        self.client.get(f"/api/v1/clinic/revenue?clinic_id={self.clinic_id}")
        snapshot = ClinicRevenueSummary.query.filter_by(clinic_id=self.clinic_id).first()
        self.assertIsNotNone(snapshot)

    def test_clinic_portal_web_routes(self):
        routes = {str(r) for r in self.app.url_map.iter_rules()}
        for route in [
            "/clinic",
            "/clinic/dashboard",
            "/clinic/bookings",
            "/clinic/orders",
            "/clinic/patients",
            "/clinic/revenue",
        ]:
            self.assertIn(route, routes)


if __name__ == "__main__":
    unittest.main()
