import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.extensions.db import db
from scripts.go_live_rc1_lib import run_e2e_workflows


class GoLiveValidationTestCase(unittest.TestCase):
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

    def test_e2e_workflows(self):
        result = run_e2e_workflows(self.app, self.client)
        self.assertGreaterEqual(result["passed"], 15)
        self.assertTrue(result["workflows"]["auth_register_login"]["ok"])
        self.assertTrue(result["workflows"]["health_readiness_liveness"]["ok"])


if __name__ == "__main__":
    unittest.main()
