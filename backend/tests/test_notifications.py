import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.core.statuses import (
    NOTIFICATION_STATUS_DELIVERED,
    NOTIFICATION_TEMPLATE_RESULT_READY,
    NOTIFICATION_TEMPLATE_WELCOME,
)
from app.extensions.db import db
from app.models.notification import Notification
from app.models.notification_delivery import NotificationDelivery
from app.services.notification_service import NotificationQueue, NotificationService
from scripts.seed_notifications_demo import seed_notifications_demo


class NotificationsTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()
        seed_notifications_demo()
        NotificationQueue.clear()

    def tearDown(self):
        NotificationQueue.clear()
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def test_notification_apis(self):
        templates = self.client.get("/api/v1/notification-templates")
        self.assertEqual(templates.status_code, 200)
        self.assertGreaterEqual(templates.get_json()["count"], 8)

        send = self.client.post(
            "/api/v1/notifications/send",
            json={
                "template_code": NOTIFICATION_TEMPLATE_RESULT_READY,
                "context": {"name": "Patient A", "order_code": "MDO-000001"},
                "recipients": [
                    {
                        "recipient_name": "Patient A",
                        "email": "patient@dxcon.vn",
                        "phone": "0909111222",
                        "push_token": "firebase-token-1",
                        "zalo_id": "zalo-123",
                    }
                ],
            },
        )
        self.assertEqual(send.status_code, 201)
        payload = send.get_json()
        self.assertEqual(payload["notification"]["status"], NOTIFICATION_STATUS_DELIVERED)
        self.assertGreaterEqual(payload["delivery_count"], 1)

        notification_id = payload["notification"]["id"]
        detail = self.client.get(f"/api/v1/notifications/{notification_id}")
        self.assertEqual(detail.status_code, 200)
        self.assertGreaterEqual(len(detail.get_json()["deliveries"]), 1)

        listing = self.client.get("/api/v1/notifications")
        self.assertEqual(listing.status_code, 200)
        self.assertGreaterEqual(listing.get_json()["count"], 1)

        bulk = self.client.post(
            "/api/v1/notifications/bulk",
            json={
                "notifications": [
                    {
                        "template_code": NOTIFICATION_TEMPLATE_WELCOME,
                        "context": {"name": "User 1"},
                        "recipients": [{"recipient_name": "User 1", "email": "u1@dxcon.vn"}],
                    },
                    {
                        "template_code": NOTIFICATION_TEMPLATE_WELCOME,
                        "context": {"name": "User 2"},
                        "recipients": [{"recipient_name": "User 2", "email": "u2@dxcon.vn"}],
                    },
                ]
            },
        )
        self.assertEqual(bulk.status_code, 201)
        self.assertEqual(bulk.get_json()["count"], 2)

        test = self.client.post("/api/v1/notifications/test", json={"email": "test@dxcon.vn"})
        self.assertEqual(test.status_code, 201)

    def test_notification_services(self):
        notification, deliveries = NotificationService.send(
            {
                "template_code": NOTIFICATION_TEMPLATE_RESULT_READY,
                "context": {"name": "Service Patient", "order_code": "MDO-000002"},
                "recipients": [
                    {
                        "recipient_name": "Service Patient",
                        "email": "service@dxcon.vn",
                        "phone": "0909333444",
                    }
                ],
                "channels": ["IN_APP", "EMAIL", "SMS"],
            }
        )
        self.assertIsNotNone(Notification.query.get(notification.id))
        self.assertGreaterEqual(len(deliveries), 2)
        self.assertGreaterEqual(
            NotificationDelivery.query.filter_by(notification_id=notification.id).count(),
            2,
        )

    def test_notification_web_routes(self):
        routes = {str(r) for r in self.app.url_map.iter_rules()}
        for route in ["/notifications", "/notification-templates"]:
            self.assertIn(route, routes)


if __name__ == "__main__":
    unittest.main()
