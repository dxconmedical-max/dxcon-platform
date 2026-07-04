import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"


class SecurityComplianceTestCase(unittest.TestCase):
    def setUp(self):
        from app import create_app
        from app.core.passwords import hash_password
        from app.extensions.db import db
        from app.models.user import User
        from app.services.api_platform_service import ApiClientService
        from app.services.enterprise_platform_service import EnterprisePlatformService

        self.app = create_app()
        self.app.config["TESTING"] = True
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()
        EnterprisePlatformService.ensure_defaults()
        ApiClientService.ensure_defaults()
        self.client = self.app.test_client()
        user = User(
            email="demo-admin-security@demo.dxcon.test",
            role="ADMIN",
            password_hash=hash_password("DemoPass123!"),
            is_active=True,
        )
        db.session.add(user)
        db.session.commit()
        with self.client.session_transaction() as sess:
            sess["user_id"] = user.id
            sess["role"] = user.role
            sess["email"] = user.email

    def tearDown(self):
        from app.extensions.db import db

        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def test_security_compliance_routes_registered(self):
        routes = {str(rule.rule) for rule in self.app.url_map.iter_rules()}
        for route in (
            "/security-compliance",
            "/security-compliance/compliance",
            "/api/v1/security-compliance/dashboard",
            "/api/v1/security-compliance/readiness",
        ):
            self.assertIn(route, routes)

    def test_dashboard_and_readiness(self):
        response = self.client.get("/security-compliance")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Security & Compliance", response.get_data(as_text=True))

        dashboard = self.client.get("/api/v1/security-compliance/dashboard")
        self.assertEqual(dashboard.status_code, 200)
        payload = dashboard.get_json()
        self.assertEqual(payload["phase"], "5.1")
        self.assertEqual(len(payload["features"]), 12)

        readiness = self.client.get("/api/v1/security-compliance/readiness")
        self.assertEqual(readiness.status_code, 200)
        self.assertIn("compliance", readiness.get_json())

    def test_legacy_routes_preserved(self):
        audit = self.client.get("/audit")
        self.assertEqual(audit.status_code, 200)
        health = self.client.get("/api/v1/admin-security/health")
        self.assertIn(health.status_code, (200, 401))


if __name__ == "__main__":
    unittest.main()
