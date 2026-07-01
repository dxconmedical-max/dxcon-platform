import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.core.statuses import NC_NOTIFICATION_SENT
from app.extensions.db import db
from app.models.notification_center import NCNotification
from app.notifications.notification_service import NotificationCenterService
from scripts.seed_notification_center_demo import seed_notification_center_demo


class NotificationCenterServiceTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()
        NotificationCenterService.ensure_defaults()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def test_create_and_list_notifications(self):
        created = self.client.post(
            "/api/v1/notifications",
            json={
                "channel": "EMAIL",
                "recipient": "patient@example.com",
                "subject": "Test",
                "body": "Hello {{patient_name}}",
                "variables": {"patient_name": "An"},
            },
        )
        self.assertEqual(created.status_code, 201)
        payload = created.get_json()
        self.assertIn("notification", payload)
        self.assertEqual(payload["notification"]["status"], NC_NOTIFICATION_SENT)

        listing = self.client.get("/api/v1/notifications")
        self.assertEqual(listing.status_code, 200)
        self.assertGreaterEqual(listing.get_json()["count"], 1)

        notification_id = payload["notification"]["id"]
        detail = self.client.get(f"/api/v1/notifications/{notification_id}")
        self.assertEqual(detail.status_code, 200)
        self.assertGreaterEqual(len(detail.get_json()["deliveries"]), 1)

    def test_statistics(self):
        seed_notification_center_demo()
        stats = self.client.get("/api/v1/notifications/statistics")
        self.assertEqual(stats.status_code, 200)
        body = stats.get_json()
        self.assertGreaterEqual(body["total"], 200)
        self.assertIn("delivery_success_rate", body)


if __name__ == "__main__":
    unittest.main()
