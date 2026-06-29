import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.core.deployment import deployment_readiness
from app.extensions.db import db
from app.models.company import Company


class HealthTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()
        self.app.extensions.setdefault("dxcon_deployment", {})
        self.app.extensions["dxcon_deployment"]["migration_status"] = {
            "ready": True,
            "table_count": 3,
        }

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def test_health_endpoint(self):
        response = self.client.get("/api/v1/system/health")
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["status"], "OK")
        self.assertIn("build", payload)

    def test_live_endpoint(self):
        response = self.client.get("/api/v1/system/live")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.get_json()["alive"])

    def test_ready_endpoint(self):
        response = self.client.get("/api/v1/system/ready")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.get_json()["ready"])

    def test_version_endpoint(self):
        response = self.client.get("/api/v1/system/version")
        self.assertEqual(response.status_code, 200)
        self.assertIn("version", response.get_json())

    def test_metrics_include_monitoring(self):
        response = self.client.get("/api/v1/system/metrics")
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertIn("memory_mb", payload)
        self.assertIn("cpu", payload)
        self.assertIn("queue", payload)
        self.assertIn("legacy", payload)


if __name__ == "__main__":
    unittest.main()
