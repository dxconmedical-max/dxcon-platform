import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.extensions.db import db
from app.infrastructure.recovery_service import RecoveryService
from app.models.infrastructure_readiness import RecoveryPlan, RecoveryReport, RecoveryTest


class RecoveryTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()
        RecoveryService.ensure_defaults()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def test_recovery_models(self):
        self.assertGreaterEqual(RecoveryPlan.query.count(), 1)
        plan = RecoveryPlan.query.first()
        self.assertGreater(plan.rto_minutes, 0)
        self.assertGreater(plan.rpo_minutes, 0)

    def test_recovery_test_run(self):
        result = RecoveryService.run_recovery_test(mode="DRY_RUN")
        self.assertEqual(result["test"]["status"], "PASSED")
        self.assertGreaterEqual(RecoveryTest.query.count(), 1)
        self.assertGreaterEqual(RecoveryReport.query.count(), 1)

    def test_recovery_api(self):
        response = self.client.get("/api/v1/infrastructure/recovery")
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertIn("plans", payload)


if __name__ == "__main__":
    unittest.main()
