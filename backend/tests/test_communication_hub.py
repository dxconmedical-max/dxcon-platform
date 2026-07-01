import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.core.statuses import (
    EVENT_BOOKING_CREATED,
    EVENT_CRITICAL_RESULT,
    NOTIFICATION_CHANNEL_EMAIL,
    NOTIFICATION_CHANNEL_PUSH,
    NOTIFICATION_CHANNEL_SMS,
    QUEUE_STATUS_COMPLETED,
    QUEUE_STATUS_DEAD_LETTER,
)
from app.extensions.db import db
from app.models.communication_hub import (
    CommunicationDeadLetter,
    CommunicationDeliveryTrack,
    CommunicationQueueItem,
    WorkflowAutomationEvent,
)
from app.services.communication_hub_service import (
    CommunicationHubService,
    EventHubService,
    QueueHubService,
)


class CommunicationHubTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()
        CommunicationHubService.ensure_defaults()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def test_notification_hub_api(self):
        summary = self.client.get("/api/v1/notifications/hub")
        self.assertEqual(summary.status_code, 200)
        self.assertIn("channels", summary.get_json())

        send = self.client.post(
            "/api/v1/notifications/hub/send",
            json={
                "recipient": "patient@example.com",
                "channels": [NOTIFICATION_CHANNEL_EMAIL, NOTIFICATION_CHANNEL_SMS],
                "subject": "Test",
                "body": "Hello",
            },
        )
        self.assertEqual(send.status_code, 201)
        self.assertGreaterEqual(CommunicationDeliveryTrack.query.count(), 1)

    def test_queue_retry_and_dead_letter(self):
        enqueue = self.client.post(
            "/api/v1/notifications/queue",
            json={
                "channel": NOTIFICATION_CHANNEL_EMAIL,
                "recipient": "",
                "payload": {"subject": "Fail", "body": "Test"},
                "max_retries": 1,
            },
        )
        self.assertEqual(enqueue.status_code, 201)
        item_id = enqueue.get_json()["id"]

        process = self.client.post("/api/v1/notifications/queue/process", json={"limit": 5})
        self.assertEqual(process.status_code, 200)

        retry = self.client.post(f"/api/v1/notifications/queue/{item_id}/retry")
        self.assertEqual(retry.status_code, 200)

        forced = self.client.post(
            "/api/v1/notifications/queue",
            json={"channel": NOTIFICATION_CHANNEL_EMAIL, "recipient": "", "max_retries": 1},
        )
        self.client.post("/api/v1/notifications/queue/process", json={"limit": 5, "force_fail": True})
        self.client.post("/api/v1/notifications/queue/process", json={"limit": 5, "force_fail": True})
        dlq = self.client.get("/api/v1/notifications/dead-letter")
        self.assertEqual(dlq.status_code, 200)
        self.assertGreaterEqual(len(dlq.get_json()["dead_letters"]), 1)

    def test_templates_api(self):
        response = self.client.get("/api/v1/templates?channel=EMAIL")
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(response.get_json()["count"], 1)

        create = self.client.post(
            "/api/v1/templates",
            json={"name": "Custom", "body": "Custom body", "channels": ["EMAIL", "PUSH"]},
        )
        self.assertEqual(create.status_code, 201)

    def test_webhooks_api(self):
        response = self.client.get("/api/v1/hub/webhooks")
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(response.get_json()["count"], 1)

        create = self.client.post(
            "/api/v1/hub/webhooks",
            json={"name": "Partner Hook", "target_url": "https://example.com/hook"},
        )
        self.assertEqual(create.status_code, 201)
        webhook_id = create.get_json()["id"]
        test = self.client.post(f"/api/v1/hub/webhooks/{webhook_id}/test", json={"event_type": "TestEvent"})
        self.assertEqual(test.status_code, 200)

    def test_events_api(self):
        types = self.client.get("/api/v1/hub/events/types")
        self.assertEqual(types.status_code, 200)
        self.assertIn(EVENT_BOOKING_CREATED, types.get_json()["event_types"])

        emit = self.client.post(
            "/api/v1/hub/events",
            json={
                "event_type": EVENT_CRITICAL_RESULT,
                "recipient": "doctor@example.com",
                "payload": {"patient_id": "P-1"},
            },
        )
        self.assertEqual(emit.status_code, 201)
        self.assertGreaterEqual(WorkflowAutomationEvent.query.count(), 1)

    def test_dashboard_pages(self):
        for path in ("/notifications", "/events", "/templates", "/webhooks"):
            response = self.client.get(path)
            self.assertEqual(response.status_code, 200, path)

    def test_services(self):
        event = EventHubService.emit(
            {"event_type": EVENT_BOOKING_CREATED, "recipient": "a@b.com", "payload": {"booking_id": "B1"}}
        )
        self.assertEqual(event["event"]["event_type"], EVENT_BOOKING_CREATED)
        queue = QueueHubService.list_queue()
        self.assertIn("queue", queue)


if __name__ == "__main__":
    unittest.main()
