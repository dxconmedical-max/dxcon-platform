import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"


class AIClinicalPlatformTestCase(unittest.TestCase):
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
            email="demo-doctor-ai@demo.dxcon.test",
            role="DOCTOR",
            password_hash=hash_password("DemoPass123!"),
            is_active=True,
        )
        db.session.add(user)
        db.session.commit()
        with self.client.session_transaction() as sess:
            sess["user_id"] = user.id
            sess["role"] = user.role
            sess["email"] = user.email

    def tearDown(self):
        from app.extensions.db import db

        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def test_ai_clinical_routes_registered(self):
        routes = {str(rule.rule) for rule in self.app.url_map.iter_rules()}
        for route in (
            "/ai-clinical",
            "/ai-clinical/providers",
            "/ai-clinical/interpret",
            "/ai-clinical/audit",
            "/api/v1/ai-clinical/dashboard",
            "/api/v1/ai-clinical/interpret",
            "/api/v1/ai-clinical/safety/disclaimer",
        ):
            self.assertIn(route, routes)

    def test_dashboard_renders_with_disclaimer(self):
        response = self.client.get("/ai-clinical")
        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertIn("AI Clinical Platform", body)
        self.assertIn("advisory only", body.lower())

    def test_api_dashboard_and_advisory_policy(self):
        response = self.client.get("/api/v1/ai-clinical/dashboard")
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["phase"], "4.2")
        self.assertFalse(payload["policy"]["automatic_diagnosis"])
        self.assertTrue(payload["policy"]["human_review_required"])
        self.assertEqual(len(payload["features"]), 15)

    def test_interpretation_audited_and_advisory(self):
        response = self.client.post(
            "/api/v1/ai-clinical/interpret",
            json={
                "items": [
                    {
                        "test_code": "GLU",
                        "test_name": "Glucose",
                        "result_value": "145",
                        "reference_range": "70-110",
                    }
                ]
            },
        )
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertTrue(payload["advisory_only"])
        self.assertTrue(payload["human_review_required"])
        self.assertTrue(payload["doctor_review_required"])
        self.assertIn("audit_id", payload)

        audit = self.client.get("/api/v1/ai-clinical/audit").get_json()
        self.assertGreaterEqual(audit["count"], 1)

    def test_phi_redaction_web_form(self):
        response = self.client.post(
            "/ai-clinical/safety",
            data={"sample_text": "Email patient@example.com"},
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("[REDACTED_EMAIL]", response.get_data(as_text=True))


if __name__ == "__main__":
    unittest.main()
