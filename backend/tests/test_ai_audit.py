import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.ai_platform.audit import AIAuditService
from app.ai_platform.inference_service import InferenceService
from app.extensions.db import db


class AIAuditTestCase(unittest.TestCase):
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
        self.ctx.pop()

    def test_inference_writes_audit(self):
        InferenceService.queue_inference(
            {
                "prompt_code": "PROMPT-INTERPRET",
                "task_type": "interpretation",
                "input": {"summary": "Test value"},
                "async": False,
            }
        )
        audit = AIAuditService.list_entries()
        actions = {entry["action"] for entry in audit["entries"]}
        self.assertIn("INFERENCE_QUEUED", actions)
        self.assertIn("INFERENCE_COMPLETED", actions)

    def test_audit_api(self):
        AIAuditService.write("TEST_ACTION", "TestResource", detail={"ok": True})
        response = self.client.get("/api/v1/ai-platform/audit")
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(response.get_json()["count"], 1)


if __name__ == "__main__":
    unittest.main()
