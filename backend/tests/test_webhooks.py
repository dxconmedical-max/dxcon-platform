import json
import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.core.statuses import INTEGRATION_WEBHOOK_DELIVERY_DELIVERED
from app.extensions.db import db
from app.models.integration_platform import WebhookDelivery, WebhookEndpoint
from app.services.integration_platform_service import IntegrationPlatformService, WebhookEngineService


class WebhookEngineTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()
        IntegrationPlatformService.ensure_defaults()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def test_register_and_sign(self):
        created = self.client.post(
            "/api/v1/webhooks",
            json={
                "name": "Partner Webhook",
                "target_url": "https://partner.example.com/hook",
                "event_types": ["OrderCreated"],
            },
        )
        self.assertEqual(created.status_code, 201)
        webhook_id = created.get_json()["id"]
        test = self.client.post(f"/api/v1/webhooks/{webhook_id}/test", json={"event_type": "OrderCreated"})
        self.assertEqual(test.status_code, 200)
        self.assertTrue(test.get_json()["signature"])

    def test_retry_delivery(self):
        webhook = WebhookEndpoint.query.first()
        result = WebhookEngineService.deliver(webhook.id, "OrderCreated", {"order_id": "O1"}, simulate_failure=True)
        delivery_id = result["delivery"]["id"]
        retried = self.client.post(f"/api/v1/webhooks/deliveries/{delivery_id}/retry")
        self.assertEqual(retried.status_code, 200)
        self.assertEqual(retried.get_json()["status"], INTEGRATION_WEBHOOK_DELIVERY_DELIVERED)

    def test_list_deliveries(self):
        response = self.client.get("/api/v1/webhooks/deliveries")
        self.assertEqual(response.status_code, 200)
        self.assertIn("deliveries", response.get_json())


if __name__ == "__main__":
    unittest.main()
