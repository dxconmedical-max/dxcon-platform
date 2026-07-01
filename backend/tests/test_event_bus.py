import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.core.statuses import DOMAIN_EVENT_ORDER_CREATED, VALID_DOMAIN_EVENTS
from app.events.domain_event import DomainEvent
from app.events.event_bus import EventBus
from app.extensions.db import db
from app.models.integration_platform import IntegrationDomainEvent, IntegrationEventDeliveryLog
from app.services.integration_platform_service import EventPlatformService, IntegrationPlatformService


class EventBusTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()
        IntegrationPlatformService.ensure_defaults()
        EventPlatformService.register_default_subscriber()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def test_publish_and_list(self):
        result = EventPlatformService.publish(
            {"event_type": DOMAIN_EVENT_ORDER_CREATED, "payload": {"order_id": "O1"}}
        )
        self.assertEqual(result["event"]["event_type"], DOMAIN_EVENT_ORDER_CREATED)
        self.assertEqual(IntegrationDomainEvent.query.count(), 1)
        self.assertGreaterEqual(IntegrationEventDeliveryLog.query.count(), 1)

        listed = self.client.get("/api/v1/events")
        self.assertEqual(listed.status_code, 200)
        self.assertGreaterEqual(listed.get_json()["count"], 1)

    def test_test_endpoint(self):
        response = self.client.post("/api/v1/events/test", json={"event_type": VALID_DOMAIN_EVENTS[0]})
        self.assertEqual(response.status_code, 201)

    def test_subscribe_handler(self):
        seen = []

        def handler(event: DomainEvent):
            seen.append(event.event_type)
            return {"ok": True}

        EventBus.subscribe(DOMAIN_EVENT_ORDER_CREATED, handler)
        EventPlatformService.publish({"event_type": DOMAIN_EVENT_ORDER_CREATED, "payload": {}})
        self.assertEqual(seen, [DOMAIN_EVENT_ORDER_CREATED])


if __name__ == "__main__":
    unittest.main()
