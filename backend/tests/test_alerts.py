import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.extensions.db import db
from app.models.observability_platform import ObsAlert


class AlertsPlatformTestCase(unittest.TestCase):
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

    def test_alert_api(self):
        listing = self.client.get("/api/v1/alerts")
        self.assertEqual(listing.status_code, 200)
        self.assertIn("platform_alerts", listing.get_json())

        test = self.client.post("/api/v1/alerts/test", json={"rule_code": "AUTH_FAILURES"})
        self.assertEqual(test.status_code, 201)
        self.assertGreaterEqual(ObsAlert.query.count(), 1)


if __name__ == "__main__":
    unittest.main()
