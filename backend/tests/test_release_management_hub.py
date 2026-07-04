import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"


class ReleaseManagementTestCase(unittest.TestCase):
    def setUp(self):
        from app import create_app
        from app.core.passwords import hash_password
        from app.extensions.db import db
        from app.models.user import User
        from app.operations.deployment_service import DeploymentService

        self.app = create_app()
        self.app.config["TESTING"] = True
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()
        DeploymentService.run_checklist()
        self.client = self.app.test_client()
        user = User(
            email="demo-admin-release@demo.dxcon.test",
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

    def test_release_management_routes_registered(self):
        routes = {str(rule.rule) for rule in self.app.url_map.iter_rules()}
        for route in (
            "/release-management",
            "/release-management/rollback",
            "/api/v1/release-management/dashboard",
            "/api/v1/release-management/readiness",
        ):
            self.assertIn(route, routes)

    def test_dashboard_and_sections(self):
        response = self.client.get("/release-management")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Release Management", response.get_data(as_text=True))

        dashboard = self.client.get("/api/v1/release-management/dashboard")
        self.assertEqual(dashboard.status_code, 200)
        payload = dashboard.get_json()
        self.assertEqual(payload["phase"], "5.7")
        self.assertEqual(len(payload["features"]), 6)

        migration = self.client.get("/api/v1/release-management/migration")
        self.assertEqual(migration.get_json()["status"], "READY")

    def test_legacy_endpoints_preserved(self):
        health = self.client.get("/api/v1/system/health")
        self.assertIn(health.status_code, {200, 503})

        deployment = self.client.get("/api/v1/operations/deployment")
        self.assertEqual(deployment.status_code, 200)


if __name__ == "__main__":
    unittest.main()
