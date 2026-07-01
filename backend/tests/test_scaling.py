import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.extensions.db import db
from app.infrastructure.scaling_advisor import ScalingAdvisor


class ScalingTestCase(unittest.TestCase):
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

    def test_scaling_advisor(self):
        advice = ScalingAdvisor.recommend(self.app)
        self.assertIn("workers", advice)
        self.assertIn("database_pool", advice)
        self.assertIn("queue", advice)
        self.assertIn("cache", advice)

    def test_scaling_api(self):
        response = self.client.get("/api/v1/infrastructure/scaling")
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertIn("workers", payload)


if __name__ == "__main__":
    unittest.main()
