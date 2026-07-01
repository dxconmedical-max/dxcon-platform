import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.extensions.db import db
from app.notifications.notification_registry import NotificationRegistry
from app.notifications.providers import (
    EmailProvider,
    InAppProvider,
    PushProvider,
    SMSProvider,
    WebhookProvider,
    ZaloOAProvider,
)
from app.notifications.notification_service import NotificationCenterService


class NotificationProviderTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()
        NotificationCenterService.ensure_defaults()

    def tearDown(self):
        NotificationRegistry._providers.clear()
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def test_provider_registry(self):
        NotificationRegistry.initialize()
        for channel in ("EMAIL", "SMS", "ZALO", "PUSH", "WEBHOOK", "IN_APP"):
            provider = NotificationRegistry.get(channel)
            self.assertTrue(hasattr(provider, "send"))
            self.assertTrue(hasattr(provider, "validate"))
            self.assertTrue(hasattr(provider, "health_check"))
            self.assertTrue(hasattr(provider, "retry"))

        providers = self.client.get("/api/v1/notifications/providers")
        self.assertEqual(providers.status_code, 200)
        self.assertGreaterEqual(providers.get_json()["count"], 6)

    def test_provider_send_demo_modes(self):
        with self.app.app_context():
            email = EmailProvider().send("user@example.com", "Subject", "Body")
            self.assertTrue(email["success"])

            sms = SMSProvider().send("+84901234567", "Subject", "Body")
            self.assertTrue(sms["success"])

            zalo = ZaloOAProvider().send("zalo-user", "Subject", "Body")
            self.assertTrue(zalo["success"])

            push = PushProvider().send("firebase-token", "Subject", "Body")
            self.assertTrue(push["success"])

            webhook = WebhookProvider().send("https://example.com/hook", "Subject", "Body")
            self.assertTrue(webhook["success"])

            in_app = InAppProvider().send("user-1", "Subject", "Body")
            self.assertTrue(in_app["success"])


if __name__ == "__main__":
    unittest.main()
