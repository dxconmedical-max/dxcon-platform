import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.extensions.db import db
from app.integrations.connector_registry import ConnectorRegistry


class ConnectorRegistryTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def test_list_and_register(self):
        listed = ConnectorRegistry.list_connectors()
        self.assertGreaterEqual(listed["count"], 1)
        created = ConnectorRegistry.register({"name": "Test LIS", "adapter_type": "LIS"})
        self.assertEqual(created["adapter_type"], "LIS")

    def test_api_endpoints(self):
        response = self.client.get("/api/v1/connectors")
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        connector_id = payload["connectors"][0]["id"]
        health = self.client.get(f"/api/v1/connectors/{connector_id}/health")
        self.assertEqual(health.status_code, 200)
        self.assertIn("healthy", health.get_json())


if __name__ == "__main__":
    unittest.main()
