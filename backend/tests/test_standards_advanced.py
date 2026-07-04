import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"


class StandardsAdvancedTestCase(unittest.TestCase):
    def setUp(self):
        from app import create_app
        from app.core.passwords import hash_password
        from app.extensions.db import db
        from app.models.user import User

        self.app = create_app()
        self.app.config["TESTING"] = True
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()
        self.client = self.app.test_client()
        user = User(
            email="demo-admin-standards@demo.dxcon.test",
            role="ADMIN",
            password_hash=hash_password("DemoPass123!"),
            is_active=True,
        )
        db.session.add(user)
        db.session.commit()
        with self.client.session_transaction() as sess:
            sess["user_id"] = user.id
            sess["role"] = user.role
            sess["email"] = user.email

        from tests.standards_test_helpers import seed_demo_data

        seed_demo_data()

    def tearDown(self):
        from app.extensions.db import db

        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def test_standards_advanced_routes_registered(self):
        routes = {str(rule.rule) for rule in self.app.url_map.iter_rules()}
        for route in (
            "/standards-advanced",
            "/standards-advanced/sandbox",
            "/api/v1/standards-advanced/dashboard",
            "/api/v1/standards-advanced/sandbox/messages",
        ):
            self.assertIn(route, routes)

    def test_dashboard_and_existing_api_preserved(self):
        response = self.client.get("/standards-advanced")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Healthcare Standards Advanced", response.get_data(as_text=True))

        legacy = self.client.get("/api/v1/standards/code-systems")
        self.assertEqual(legacy.status_code, 200)
        self.assertGreaterEqual(legacy.get_json()["count"], 1)

    def test_hl7_and_fhir_advanced_flows(self):
        sandbox = self.client.get("/api/v1/standards-advanced/sandbox/messages").get_json()
        oru = self.client.post(
            "/api/v1/standards-advanced/hl7/oru/export",
            json={"patient_id": "PAT-001", "order_id": "ORD-001", "value": "95"},
        )
        self.assertEqual(oru.status_code, 200)
        self.assertEqual(oru.get_json()["message_type"], "ORU")

        orm = self.client.post(
            "/api/v1/standards-advanced/hl7/orm/import",
            json={"message": sandbox["hl7"]["orm"]},
        )
        self.assertEqual(orm.status_code, 200)
        self.assertIn("normalized", orm.get_json())

        patient = self.client.post(
            "/api/v1/standards-advanced/fhir/patient/map",
            json={"patient_id": "PAT-001", "name": "Demo^Patient"},
        )
        self.assertEqual(patient.status_code, 200)
        self.assertEqual(patient.get_json()["resource"]["resourceType"], "Patient")

    def test_code_validation_and_audit(self):
        loinc = self.client.post("/api/v1/standards-advanced/loinc/validate", json={"code": "LNC-0001"})
        self.assertTrue(loinc.get_json()["valid"])

        icd = self.client.post("/api/v1/standards-advanced/icd10/validate", json={"code": "I10-0001"})
        self.assertTrue(icd.get_json()["valid"])

        audit = self.client.get("/api/v1/standards-advanced/audit")
        self.assertGreaterEqual(audit.get_json()["count"], 1)


if __name__ == "__main__":
    unittest.main()
