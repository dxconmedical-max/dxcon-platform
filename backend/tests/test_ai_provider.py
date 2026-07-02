import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.ai_platform.registry import AIProviderRegistry
from app.extensions.db import db


class AIProviderTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        AIProviderRegistry.reset()
        self.ctx.pop()

    def test_list_defaults(self):
        payload = AIProviderRegistry.list_providers()
        self.assertGreaterEqual(payload["count"], 1)

    def test_register_provider(self):
        created = AIProviderRegistry.register(
            {"name": "OpenAI Stub", "provider_type": "OPENAI_COMPATIBLE", "model_name": "gpt-stub"}
        )
        self.assertEqual(created["provider_type"], "OPENAI_COMPATIBLE")

    def test_api_list_providers(self):
        response = self.client.get("/api/v1/ai-platform/providers")
        self.assertEqual(response.status_code, 200)
        self.assertIn("providers", response.get_json())


if __name__ == "__main__":
    unittest.main()
