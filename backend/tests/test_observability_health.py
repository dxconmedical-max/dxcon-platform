import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.extensions.db import db


class ObservabilityHealthTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()
        self.app.extensions.setdefault("dxcon_deployment", {})
        self.app.extensions["dxcon_deployment"]["migration_status"] = {"ready": True}

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def test_root_health_probes(self):
        for path in ("/health", "/ready", "/live", "/api/v1/system/health"):
            response = self.client.get(path)
            self.assertIn(response.status_code, (200, 503), path)

    def test_health_components(self):
        response = self.client.get("/health")
        payload = response.get_json()
        self.assertIn("components", payload)
        self.assertGreaterEqual(len(payload["components"]), 8)


if __name__ == "__main__":
    unittest.main()
