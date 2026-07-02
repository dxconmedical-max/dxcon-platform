import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.extensions.db import db
from app.services.integration_platform_service import IntegrationPlatformService, WebhookEngineService


class WebhookIdempotencyTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()
        IntegrationPlatformService.ensure_defaults()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def test_idempotent_delivery(self):
        webhook = __import__("app.models.integration_platform", fromlist=["WebhookEndpoint"]).WebhookEndpoint.query.first()
        key = "test-idempotency-key"
        first = WebhookEngineService.deliver(webhook.id, "OrderCreated", {"order_id": "1"}, idempotency_key=key)
        second = WebhookEngineService.deliver(webhook.id, "OrderCreated", {"order_id": "1"}, idempotency_key=key)
        self.assertEqual(first["delivery"]["id"], second["delivery"]["id"])


if __name__ == "__main__":
    unittest.main()
