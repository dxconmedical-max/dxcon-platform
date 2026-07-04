import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"


class IntegrationHubTestCase(unittest.TestCase):
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
            email="demo-admin-hub@demo.dxcon.test",
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

    def tearDown(self):
        from app.extensions.db import db

        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def test_integration_hub_routes_registered(self):
        routes = {str(rule.rule) for rule in self.app.url_map.iter_rules()}
        for route in (
            "/integration-hub",
            "/integration-hub/connectors",
            "/integration-hub/adapters",
            "/integration-hub/webhooks",
            "/integration-hub/api-keys",
            "/integration-hub/retry-queue",
            "/integration-hub/dead-letters",
            "/integration-hub/audit",
            "/integration-hub/sandbox",
            "/api/v1/integration-hub/dashboard",
            "/api/v1/integration-hub/sandbox/test",
        ):
            self.assertIn(route, routes)

    def test_dashboard_renders(self):
        response = self.client.get("/integration-hub")
        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertIn("Integration Center", body)
        self.assertIn("Connector Registry", body)

    def test_api_dashboard_and_adapters(self):
        response = self.client.get("/api/v1/integration-hub/dashboard")
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["phase"], "4.1")
        self.assertIn("summary", payload)
        self.assertEqual(len(payload["features"]), 15)

        adapters = self.client.get("/api/v1/integration-hub/adapters").get_json()
        adapter_types = {item["type"] for item in adapters["adapters"]}
        for adapter in ("HIS", "LIS", "EMR", "ERP", "INSURANCE", "PAYMENT"):
            self.assertIn(adapter, adapter_types)

    def test_sandbox_test_and_audit(self):
        response = self.client.post(
            "/api/v1/integration-hub/sandbox/test",
            json={"adapter_type": "EMR", "payload": {"record_id": "TEST-EMR"}},
        )
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertTrue(payload["sandbox"])
        self.assertIn("audit_id", payload)

        audit = self.client.get("/api/v1/integration-hub/audit").get_json()
        self.assertGreaterEqual(audit["count"], 1)

    def test_sandbox_web_form(self):
        response = self.client.post(
            "/integration-hub/sandbox",
            data={"adapter_type": "LIS", "payload": '{"result_id":"WEB-001"}'},
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("Sandbox Result", response.get_data(as_text=True))


if __name__ == "__main__":
    unittest.main()
