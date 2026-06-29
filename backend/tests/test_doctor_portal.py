import os
import sys
import unittest
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.core.statuses import MAPPING_ACTIVE, PARTNER_ACTIVE
from app.extensions.db import db
from app.models.company import Company
from app.models.diagnostic_category import DiagnosticCategory
from app.models.diagnostic_service import DiagnosticService
from app.models.doctor_profile import DoctorProfile
from app.models.doctor_dashboard import DoctorDashboard
from app.models.partner import Partner
from app.models.partner_service_mapping import PartnerServiceMapping
from app.services.slot_generation import SlotGenerationService
from scripts.seed_doctor_portal_demo import seed_doctor_portal_demo, seed_doctor_portal_flow


class DoctorPortalTestCase(unittest.TestCase):
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
            partner_code="PTR-DOC-001",
            partner_type="LABORATORY",
            legal_name="Doctor Portal Lab",
            display_name="Doctor Portal Lab",
            status=PARTNER_ACTIVE,
        )
        db.session.add(self.partner)
        db.session.flush()
        self.mapping = PartnerServiceMapping(
            partner_id=self.partner.id,
            diagnostic_service_id=svc.id,
            partner_service_code="DOC-GLU",
            partner_service_name="Glucose",
            price=120000,
            status=MAPPING_ACTIVE,
        )
        db.session.add(self.mapping)
        db.session.commit()
        SlotGenerationService.generate_partner_daily_slots(self.partner.id, days=2)
        seed_doctor_portal_demo()
        self.flow = seed_doctor_portal_flow(self.partner, self.mapping)
        self.doctor_id = self.flow["doctor_id"]
        self.patient_id = self.flow["patient_id"]

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def test_doctor_portal_apis(self):
        did = self.doctor_id
        pid = self.patient_id

        dashboard = self.client.get(f"/api/v1/doctor/dashboard?doctor_id={did}")
        self.assertEqual(dashboard.status_code, 200)
        self.assertGreaterEqual(dashboard.get_json()["summary"]["patients_total"], 1)

        profile = self.client.get(f"/api/v1/doctor/profile?doctor_id={did}")
        self.assertEqual(profile.status_code, 200)

        update = self.client.put(
            f"/api/v1/doctor/profile?doctor_id={did}",
            json={"bio": "Updated bio"},
        )
        self.assertEqual(update.status_code, 200)

        patients = self.client.get(f"/api/v1/doctor/patients?doctor_id={did}")
        self.assertEqual(patients.status_code, 200)
        self.assertGreaterEqual(patients.get_json()["count"], 1)

        results = self.client.get(f"/api/v1/doctor/results?doctor_id={did}")
        self.assertEqual(results.status_code, 200)

        referral = self.client.post(
            f"/api/v1/doctor/referrals?doctor_id={did}",
            json={
                "patient_id": pid,
                "test_code": "HBA1C",
                "test_name": "HbA1c",
                "partner_id": self.partner.id,
            },
        )
        self.assertEqual(referral.status_code, 201)

        referrals = self.client.get(f"/api/v1/doctor/referrals?doctor_id={did}")
        self.assertEqual(referrals.status_code, 200)
        self.assertGreaterEqual(referrals.get_json()["count"], 1)

        follow_up = self.client.post(
            f"/api/v1/doctor/followups?doctor_id={did}",
            json={
                "patient_id": pid,
                "follow_up_date": (datetime.utcnow() + timedelta(days=7)).isoformat(),
                "note_text": "Review glucose result",
            },
        )
        self.assertEqual(follow_up.status_code, 201)

        schedule = self.client.get(f"/api/v1/doctor/schedule?doctor_id={did}")
        self.assertEqual(schedule.status_code, 200)

    def test_doctor_portal_services(self):
        profile = DoctorProfile.query.filter_by(doctor_id=self.doctor_id).first()
        self.assertIsNotNone(profile)
        self.client.get(f"/api/v1/doctor/dashboard?doctor_id={self.doctor_id}")
        snapshot = DoctorDashboard.query.filter_by(doctor_id=self.doctor_id).first()
        self.assertIsNotNone(snapshot)

    def test_doctor_portal_web_routes(self):
        routes = {str(r) for r in self.app.url_map.iter_rules()}
        for route in [
            "/doctor",
            "/doctor/dashboard",
            "/doctor/patients",
            "/doctor/results",
            "/doctor/referrals",
        ]:
            self.assertIn(route, routes)


if __name__ == "__main__":
    unittest.main()
