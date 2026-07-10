"""Tests for AI Platform Core — Epic 9."""

from __future__ import annotations

import os
import unittest

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

from app import create_app
from app.extensions.db import db
from app.ai_platform.gateway import AIGateway
from app.ai_platform.governance import AIGovernanceService
from app.ai_platform.memory import AIMemoryService
from app.ai_platform.rag import AIRagService
from app.ai_platform.sdk import AIPlatformClient


class AIPlatformCoreTests(unittest.TestCase):
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

    def test_sdk_manifest(self):
        res = self.client.get("/api/v1/ai-platform/sdk/manifest")
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.get_json().get("gateway_only"))

    def test_governance_blocks_unknown_task(self):
        with self.app.app_context():
            AIGovernanceService.ensure_default_policy()
            result = AIGovernanceService.evaluate_request("forbidden_task_type")
        self.assertFalse(result["allowed"])

    def test_memory_session(self):
        with self.app.app_context():
            session = AIMemoryService.create_session(organization_id="org-1", user_id="u-1")
            AIMemoryService.append_message(session["id"], "user", "patient@example.com glucose")
            loaded = AIMemoryService.get_session(session["id"])
        self.assertEqual(len(loaded["messages"]), 1)
        self.assertIn("[REDACTED_EMAIL]", loaded["messages"][0]["content_redacted"])

    def test_rag_retrieve(self):
        with self.app.app_context():
            AIRagService.ingest_document(
                organization_id="org-1",
                title="HbA1c",
                content="HbA1c elevation suggests glycemic control review by physician.",
            )
            hits = AIRagService.retrieve("glycemic physician", organization_id="org-1")
        self.assertGreaterEqual(hits["count"], 1)

    def test_gateway_infer(self):
        with self.app.app_context():
            from app.ai_platform.prompt_registry import PromptRegistry

            PromptRegistry.ensure_defaults()
            result = AIGateway.infer(
                {
                    "prompt_code": "PROMPT-INTERPRET",
                    "task_type": "interpretation",
                    "input": {"summary": "Glucose borderline"},
                    "async": False,
                },
                actor="doctor@test.com",
                organization_id="org-1",
                user_id="u-1",
            )
        self.assertEqual(result["status"], "COMPLETED")
        self.assertTrue(result["output"].get("human_review_required"))

    def test_sdk_client_wrapper(self):
        class FakeHTTP:
            def get(self, path, headers=None):
                return {"path": path}

        client = AIPlatformClient(FakeHTTP())
        payload = client.sdk_manifest()
        self.assertIn("/api/v1/ai-platform/sdk/manifest", payload["path"])


if __name__ == "__main__":
    unittest.main()
