import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.core.audit_logger import log_audit_event
from app.core.build_info import build_info
from app.core.deployment import deployment_readiness
from app.extensions.db import db


class DeploymentTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()
        self.app.extensions.setdefault("dxcon_deployment", {})
        self.app.extensions["dxcon_deployment"]["migration_status"] = {"ready": True}

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def test_build_info(self):
        info = build_info()
        self.assertIn("version", info)
        self.assertIn("git_sha", info)

    def test_deployment_readiness_score(self):
        readiness = deployment_readiness(self.app)
        self.assertIn("score", readiness)
        self.assertIn("checks", readiness)
        self.assertGreaterEqual(readiness["score"], 0)

    def test_build_endpoint(self):
        response = self.client.get("/api/v1/system/build")
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertIn("readiness", payload)

    def test_correlation_id_header(self):
        response = self.client.get(
            "/api/v1/system/live",
            headers={"X-Correlation-ID": "corr-test-001"},
        )
        self.assertEqual(response.headers.get("X-Correlation-ID"), "corr-test-001")

    def test_audit_logger(self):
        with self.app.test_request_context(
            "/api/v1/system/live",
            headers={
                "X-Request-ID": "req-audit-001",
                "X-Correlation-ID": "corr-audit-001",
            },
        ):
            log_audit_event("DEPLOY_TEST", "SYSTEM", "1")
            db.session.commit()
            from app.models.audit_log import AuditLog

            audit = AuditLog.query.order_by(AuditLog.created_at.desc()).first()
            self.assertEqual(audit.request_id, "req-audit-001")

    def test_gunicorn_config_exists(self):
        config_path = ROOT / "gunicorn.conf.py"
        self.assertTrue(config_path.exists())


if __name__ == "__main__":
    unittest.main()
