import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.extensions.db import db
from app.models.notification_center import NCNotificationTemplate
from app.notifications.notification_service import NotificationCenterService


class NotificationTemplateTestCase(unittest.TestCase):
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

    def test_template_crud(self):
        create = self.client.post(
            "/api/v1/notifications/templates",
            json={
                "name": "Result Ready",
                "channel": "EMAIL",
                "language": "vi",
                "subject": "Result for {{order_code}}",
                "body": "Hello {{patient_name}}, view {{result_url}}",
                "variables": ["patient_name", "order_code", "result_url"],
            },
        )
        self.assertEqual(create.status_code, 201)
        template_id = create.get_json()["id"]

        listing = self.client.get("/api/v1/notifications/templates")
        self.assertEqual(listing.status_code, 200)
        self.assertGreaterEqual(listing.get_json()["count"], 1)

        update = self.client.put(
            f"/api/v1/notifications/templates/{template_id}",
            json={"name": "Updated Result Ready", "language": "en"},
        )
        self.assertEqual(update.status_code, 200)
        self.assertEqual(update.get_json()["name"], "Updated Result Ready")

        row = NCNotificationTemplate.query.filter_by(id=template_id).first()
        self.assertEqual(row.language, "en")


if __name__ == "__main__":
    unittest.main()
