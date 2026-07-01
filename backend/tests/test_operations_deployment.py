import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.extensions.db import db


class OperationsDeploymentTestCase(unittest.TestCase):
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

    def test_deployment_api(self):
        current = self.client.get("/api/v1/operations/deployment")
        self.assertEqual(current.status_code, 200)
        self.assertIn("current_version", current.get_json())

        check = self.client.post("/api/v1/operations/deployment/check")
        self.assertEqual(check.status_code, 201)
        self.assertIn("deployment", check.get_json())

        rollback = self.client.get("/api/v1/operations/deployment/rollback-plan")
        self.assertEqual(rollback.status_code, 200)


if __name__ == "__main__":
    unittest.main()
