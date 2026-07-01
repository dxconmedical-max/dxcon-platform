import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.extensions.db import db
from scripts.go_live_rc2_lib import run_final_smoke


class FinalSmokeTestCase(unittest.TestCase):
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

    def test_final_smoke_path(self):
        result = run_final_smoke(self.app, self.client)
        self.assertGreaterEqual(result["passed"], 12)
        self.assertTrue(result["steps"]["register_login"]["ok"])
        self.assertTrue(result["steps"]["release_result"]["ok"])
        self.assertTrue(result["steps"]["billing_invoice"]["ok"])


if __name__ == "__main__":
    unittest.main()
