import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.core.statuses import VALID_DOMAIN_EVENTS
from app.events.deduplication import EventDeduplicationService
from app.events.domain_event import DomainEvent
from app.events.event_bus import EventBus
from app.extensions.db import db


class EventDeduplicationTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def test_duplicate_event_blocked(self):
        event_type = VALID_DOMAIN_EVENTS[0]
        payload = {"order_id": "DEDUP-1"}
        event = DomainEvent(event_type=event_type, payload=payload, source="test")
        first = EventBus.publish(event)
        second = EventBus.publish(DomainEvent(event_type=event_type, payload=payload, source="test"))
        self.assertFalse(first["event"].get("deduplicated"))
        self.assertTrue(second["event"].get("deduplicated"))

    def test_fingerprint_service(self):
        fp1 = EventDeduplicationService.fingerprint("OrderCreated", {"a": 1})
        fp2 = EventDeduplicationService.fingerprint("OrderCreated", {"a": 1})
        fp3 = EventDeduplicationService.fingerprint("OrderCreated", {"a": 2})
        self.assertEqual(fp1, fp2)
        self.assertNotEqual(fp1, fp3)


if __name__ == "__main__":
    unittest.main()
