"""Tests for Clinical AI Assistant — Epic 10."""

from __future__ import annotations

import os
import unittest

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

from app import create_app
from app.extensions.db import db
from app.clinical_ai.assistant import assistant_interpret, assistant_policy


class ClinicalAIAssistantTests(unittest.TestCase):
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

    def test_policy_gateway_only(self):
        policy = assistant_policy()
        self.assertTrue(policy["gateway_only"])
        self.assertTrue(policy["doctor_review_required"])

    def test_assistant_interpret_api(self):
        res = self.client.post(
            "/api/v1/ai-clinical/assistant/interpret",
            json={"items": [{"test_name": "Glucose", "test_code": "GLU", "result_value": "6.1", "reference_range": "3.9-5.5"}]},
        )
        self.assertEqual(res.status_code, 200)
        payload = res.get_json()
        self.assertTrue(payload.get("doctor_review_required"))
        self.assertTrue(payload.get("gateway_only"))


if __name__ == "__main__":
    unittest.main()
