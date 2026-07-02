import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.ai_platform.prompt_registry import PromptRegistry
from app.extensions.db import db


class PromptRegistryTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()
        PromptRegistry.ensure_defaults()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def test_defaults_seeded(self):
        payload = PromptRegistry.list_prompts()
        self.assertGreaterEqual(payload["count"], 2)

    def test_versioning(self):
        first = PromptRegistry.register(
            {
                "prompt_code": "PROMPT-UNIT",
                "name": "Unit Prompt",
                "task_type": "summary",
                "template_text": "Version 1",
            }
        )
        second = PromptRegistry.register({"prompt_code": "PROMPT-UNIT", "template_text": "Version 2"})
        self.assertEqual(first["version"]["version"], 1)
        self.assertEqual(second["version"]["version"], 2)
        self.assertEqual(second["prompt"]["active_version"], 2)


if __name__ == "__main__":
    unittest.main()
