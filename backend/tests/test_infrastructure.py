import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.extensions.db import db
from app.infrastructure.infrastructure_services import InfrastructureHealthService, InfrastructureReadinessService
from app.infrastructure.runtime_validation import RuntimeValidationService


class InfrastructureTestCase(unittest.TestCase):
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

    def test_runtime_validation(self):
        result = RuntimeValidationService.validate_all(self.app)
        self.assertIn("status", result)
        self.assertEqual(len(result["checks"]), len(RuntimeValidationService.CHECKS))

    def test_health_service(self):
        status = InfrastructureHealthService.status(self.app)
        self.assertIn("deployment_score", status)
        self.assertIn("components", status)

    def test_readiness_service(self):
        readiness = InfrastructureReadinessService.readiness(self.app)
        self.assertIn("ready", readiness)

    def test_infrastructure_api(self):
        status = self.client.get("/api/v1/infrastructure/status")
        self.assertEqual(status.status_code, 200)
        self.assertIn("status", status.get_json())

        config = self.client.get("/api/v1/infrastructure/config")
        self.assertEqual(config.status_code, 200)
        self.assertIn("profile", config.get_json())


if __name__ == "__main__":
    unittest.main()
