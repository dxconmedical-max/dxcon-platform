import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.extensions.db import db
from app.operations.secret_rotation_service import SecretRotationService


class OperationsSecretsTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()
        SecretRotationService.ensure_defaults()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def test_secret_rotation_api(self):
        listing = self.client.get("/api/v1/operations/secrets")
        self.assertEqual(listing.status_code, 200)
        self.assertGreaterEqual(listing.get_json()["count"], 1)

        validate = self.client.post("/api/v1/operations/secrets/validate")
        self.assertEqual(validate.status_code, 200)
        self.assertIn("validated", validate.get_json())

        plan_id = listing.get_json()["secrets"][0]["id"]
        rotated = self.client.post(f"/api/v1/operations/secrets/{plan_id}/mark-rotated")
        self.assertEqual(rotated.status_code, 200)


if __name__ == "__main__":
    unittest.main()
