import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.extensions.db import db
from app.services.integration_platform_service import IntegrationPlatformService


class IntegrationSandboxTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()
        IntegrationPlatformService.ensure_defaults()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def test_sandbox_status(self):
        response = self.client.get("/api/v1/sandbox/status")
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertTrue(payload["sandbox"])
        self.assertGreaterEqual(payload["adapters"], 8)

    def test_sandbox_endpoints(self):
        lis = self.client.post("/api/v1/sandbox/lis/result", json={"result_id": "R1"})
        self.assertEqual(lis.status_code, 201)
        his = self.client.post("/api/v1/sandbox/his/patient", json={"patient_id": "P1"})
        self.assertEqual(his.status_code, 201)
        payment = self.client.post("/api/v1/sandbox/payment/callback", json={"transaction_id": "T1"})
        self.assertEqual(payment.status_code, 201)
        webhook = self.client.post("/api/v1/sandbox/webhook/test", json={})
        self.assertEqual(webhook.status_code, 200)

    def test_dashboard_routes(self):
        for path in (
            "/integrations/platform",
            "/integrations/adapters",
            "/integrations/plugins",
            "/integrations/events",
            "/integrations/webhooks",
            "/integrations/queue",
            "/integrations/sandbox",
        ):
            response = self.client.get(path)
            self.assertEqual(response.status_code, 200, path)


if __name__ == "__main__":
    unittest.main()
