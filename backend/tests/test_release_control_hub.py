import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"


class ReleaseControlTestCase(unittest.TestCase):
    def setUp(self):
        from app import create_app
        from app.core.passwords import hash_password
        from app.extensions.db import db
        from app.models.user import User

        self.app = create_app()
        self.app.config["TESTING"] = True
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()
        self.client = self.app.test_client()
        user = User(
            email="demo-admin-release-control@demo.dxcon.test",
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

    def test_release_control_routes_registered(self):
        routes = {str(rule.rule) for rule in self.app.url_map.iter_rules()}
        for route in (
            "/release-control",
            "/release-control/audit",
            "/api/v1/release-control/dashboard",
            "/api/v1/release-control/readiness",
        ):
            self.assertIn(route, routes)

    def test_dashboard_and_sections(self):
        response = self.client.get("/release-control")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Release Control", response.get_data(as_text=True))

        dashboard = self.client.get("/api/v1/release-control/dashboard")
        self.assertEqual(dashboard.status_code, 200)
        payload = dashboard.get_json()
        self.assertEqual(payload["phase"], "5.12")
        self.assertEqual(len(payload["features"]), 6)

        compare = self.client.get("/api/v1/release-control/version-compare")
        self.assertIn("differences", compare.get_json())

        audit = self.client.get("/api/v1/release-control/audit")
        self.assertIn("audit_entries", audit.get_json())

    def test_legacy_release_management_preserved(self):
        mgmt = self.client.get("/release-management")
        self.assertEqual(mgmt.status_code, 200)
        prod = self.client.get("/production-deployment")
        self.assertEqual(prod.status_code, 200)


if __name__ == "__main__":
    unittest.main()
