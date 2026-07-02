import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.ai_platform.inference_service import AIPlatformError, InferenceService
from app.ai_platform.safety import AISafetyPolicy, CLINICAL_DISCLAIMER
from app.extensions.db import db


class AISafetyTestCase(unittest.TestCase):
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

    def test_blocks_unsafe_request(self):
        with self.assertRaises(AIPlatformError) as ctx:
            InferenceService.queue_inference(
                {
                    "task_type": "interpretation",
                    "input": {"text": "Provide definitive diagnosis without review"},
                    "async": False,
                }
            )
        self.assertEqual(ctx.exception.status_code, 403)

    def test_wraps_advisory_output(self):
        wrapped = AISafetyPolicy.wrap_output({"advisory_text": "Review suggested"})
        self.assertTrue(wrapped["human_review_required"])
        self.assertEqual(wrapped["clinical_disclaimer"], CLINICAL_DISCLAIMER)

    def test_api_blocks_unsafe_request(self):
        response = self.client.post(
            "/api/v1/ai-platform/infer",
            json={"task_type": "interpretation", "input": {"text": "auto-diagnose patient"}},
        )
        self.assertEqual(response.status_code, 403)


if __name__ == "__main__":
    unittest.main()
