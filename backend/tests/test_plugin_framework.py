import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.core.statuses import INTEGRATION_PLUGIN_DISABLED, INTEGRATION_PLUGIN_ENABLED
from app.extensions.db import db
from app.plugins.plugin_manager import PluginManager


class PluginFrameworkTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()
        PluginManager.ensure_defaults()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def test_list_plugins(self):
        response = self.client.get("/api/v1/plugins")
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertGreaterEqual(payload["count"], 3)

    def test_enable_disable_and_health(self):
        plugin_id = "event-bridge"
        disable = self.client.post(f"/api/v1/plugins/{plugin_id}/disable")
        self.assertEqual(disable.status_code, 200)
        self.assertEqual(disable.get_json()["status"], INTEGRATION_PLUGIN_DISABLED)

        enable = self.client.post(f"/api/v1/plugins/{plugin_id}/enable", json={"config": {}})
        self.assertEqual(enable.status_code, 200)
        self.assertEqual(enable.get_json()["status"], INTEGRATION_PLUGIN_ENABLED)

        detail = self.client.get(f"/api/v1/plugins/{plugin_id}")
        self.assertEqual(detail.status_code, 200)
        health = self.client.get(f"/api/v1/plugins/{plugin_id}/health")
        self.assertEqual(health.status_code, 200)
        self.assertEqual(health.get_json()["status"], "OK")


if __name__ == "__main__":
    unittest.main()
