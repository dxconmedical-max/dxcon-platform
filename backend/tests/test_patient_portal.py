import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.core.statuses import (
    LAB_RESULT_RELEASED,
    MAPPING_ACTIVE,
    PARTNER_ACTIVE,
    PATIENT_CONSENT_DATA_PROCESSING,
)
from app.extensions.db import db
from app.models.company import Company
from app.models.diagnostic_category import DiagnosticCategory
from app.models.diagnostic_service import DiagnosticService
from app.models.lab_result import LabResult
from app.models.partner import Partner
from app.models.partner_service_mapping import PartnerServiceMapping
from app.models.patient import Patient
from app.models.patient_profile import PatientProfile
from app.services.patient_portal_service import PatientPortalService
from app.services.slot_generation import SlotGenerationService
from scripts.seed_patient_portal_demo import seed_patient_portal_demo, seed_patient_portal_flow


class PatientPortalTestCase(unittest.TestCase):
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
            partner_code="PTR-PP-001",
            partner_type="LABORATORY",
            legal_name="Patient Portal Lab",
            display_name="Patient Portal Lab",
            status=PARTNER_ACTIVE,
        )
        db.session.add(self.partner)
        db.session.flush()
        self.mapping = PartnerServiceMapping(
            partner_id=self.partner.id,
            diagnostic_service_id=svc.id,
            partner_service_code="PP-GLU",
            partner_service_name="Glucose",
            price=120000,
            status=MAPPING_ACTIVE,
        )
        db.session.add(self.mapping)
        db.session.commit()
        SlotGenerationService.generate_partner_daily_slots(self.partner.id, days=2)
        seed_patient_portal_demo()
        self.patient = Patient.query.filter_by(phone="0908111999").first()
        seed_patient_portal_flow(self.mapping)

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def test_patient_portal_apis(self):
        pid = self.patient.id

        dashboard = self.client.get(f"/api/v1/patient/dashboard?patient_id={pid}")
        self.assertEqual(dashboard.status_code, 200)
        self.assertGreaterEqual(dashboard.get_json()["summary"]["orders_total"], 1)

        profile = self.client.get(f"/api/v1/patient/profile?patient_id={pid}")
        self.assertEqual(profile.status_code, 200)
        self.assertIn("qr_profile", profile.get_json())

        update = self.client.put(
            f"/api/v1/patient/profile?patient_id={pid}",
            json={
                "language": "en",
                "favorite_doctors": [{"doctor_id": "DOC-002", "name": "Dr. Binh"}],
            },
        )
        self.assertEqual(update.status_code, 200)

        results = self.client.get(f"/api/v1/patient/results?patient_id={pid}")
        self.assertEqual(results.status_code, 200)
        self.assertGreaterEqual(results.get_json()["count"], 1)

        orders = self.client.get(f"/api/v1/patient/orders?patient_id={pid}")
        self.assertEqual(orders.status_code, 200)
        self.assertGreaterEqual(orders.get_json()["count"], 1)

        timeline = self.client.get(f"/api/v1/patient/timeline?patient_id={pid}")
        self.assertEqual(timeline.status_code, 200)
        self.assertGreaterEqual(timeline.get_json()["count"], 1)

        notifications = self.client.get(f"/api/v1/patient/notifications?patient_id={pid}")
        self.assertEqual(notifications.status_code, 200)

        consent = self.client.post(
            f"/api/v1/patient/consent?patient_id={pid}",
            json={"consent_type": PATIENT_CONSENT_DATA_PROCESSING, "granted": True},
        )
        self.assertEqual(consent.status_code, 201)

        lab_result = LabResult.query.filter_by(status=LAB_RESULT_RELEASED).first()
        share = self.client.post(
            f"/api/v1/patient/share-report?patient_id={pid}",
            json={"lab_result_id": lab_result.id},
        )
        self.assertEqual(share.status_code, 201)
        self.assertIn("share_code", share.get_json()["share"])

    def test_patient_portal_services(self):
        profile = PatientPortalService._ensure_profile(self.patient.id)
        self.assertIsNotNone(PatientProfile.query.get(profile.id))

    def test_patient_portal_web_routes(self):
        routes = {str(r) for r in self.app.url_map.iter_rules()}
        for route in [
            "/patient",
            "/patient/profile",
            "/patient/results",
            "/patient/orders",
            "/patient/timeline",
        ]:
            self.assertIn(route, routes)


if __name__ == "__main__":
    unittest.main()
