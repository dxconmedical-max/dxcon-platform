import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.core.startup_checks import run_startup_checks
from app.extensions.db import db
from app.observability.health_service import HealthPlatformService


class ObservabilityHealthRegressionTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()
        self.app.extensions.setdefault("dxcon_deployment", {})
        self.app.extensions["dxcon_deployment"]["migration_status"] = {"ready": True}

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def test_check_application_reads_cached_startup_dict(self):
        run_startup_checks(self.app)
        cached = self.app.extensions["dxcon_startup"]["checks"]
        self.assertIsInstance(cached, dict)
        result = HealthPlatformService.check_application()
        self.assertIn(result["status"], {"OK", "DEGRADED"})
        self.assertIsInstance(result["checks"], list)
        self.assertGreaterEqual(len(result["checks"]), 4)

    def test_evaluate_does_not_mark_application_down(self):
        run_startup_checks(self.app)
        payload = HealthPlatformService.evaluate()
        application = payload["components"][0]
        self.assertNotEqual(application["status"], "DOWN")
        self.assertNotEqual(payload["status"], "DOWN")


if __name__ == "__main__":
    unittest.main()
