import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.core.statuses import (
    DOMAIN_EVENT_BOOKING_CREATED,
    DOMAIN_EVENT_CRITICAL_RESULT,
    DOMAIN_EVENT_INVOICE_CREATED,
)
from app.events.domain_event import DomainEvent
from app.events.event_bus import EventBus
from app.extensions.db import db
from app.models.notification_center import NCNotification
from app.notifications.notification_service import NotificationCenterService, NotificationEventSubscriber
from app.services.integration_platform_service import IntegrationPlatformService


class NotificationEventsTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()
        IntegrationPlatformService.ensure_defaults()
        NotificationCenterService.ensure_defaults()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def test_event_subscriptions_registered(self):
        subscribed = NotificationEventSubscriber.register()
        self.assertIn(DOMAIN_EVENT_BOOKING_CREATED, subscribed["subscribed"])
        self.assertIn(DOMAIN_EVENT_INVOICE_CREATED, subscribed["subscribed"])

    def test_event_bus_creates_notification(self):
        before = NCNotification.query.count()
        EventBus.publish(
            DomainEvent(
                event_type=DOMAIN_EVENT_BOOKING_CREATED,
                payload={"recipient": "booking@example.com", "patient_name": "Patient A"},
                source="test",
            )
        )
        self.assertGreater(NCNotification.query.count(), before)

    def test_critical_event_uses_sms(self):
        EventBus.publish(
            DomainEvent(
                event_type=DOMAIN_EVENT_CRITICAL_RESULT,
                payload={"recipient": "+84901112233", "patient_name": "Critical Patient"},
                source="test",
            )
        )
        row = NCNotification.query.order_by(NCNotification.created_at.desc()).first()
        self.assertEqual(row.channel, "SMS")
        self.assertEqual(row.priority, "CRITICAL")


if __name__ == "__main__":
    unittest.main()
