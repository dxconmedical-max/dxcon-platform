import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"


class EnterpriseAnalyticsTestCase(unittest.TestCase):
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
            email="demo-admin-analytics@demo.dxcon.test",
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

    def test_enterprise_analytics_routes_registered(self):
        routes = {str(rule.rule) for rule in self.app.url_map.iter_rules()}
        for route in (
            "/enterprise-analytics",
            "/enterprise-analytics/export",
            "/api/v1/enterprise-analytics/dashboard",
            "/api/v1/enterprise-analytics/export",
        ):
            self.assertIn(route, routes)

    def test_dashboard_and_read_only_api(self):
        response = self.client.get("/enterprise-analytics")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Enterprise Analytics", response.get_data(as_text=True))

        dashboard = self.client.get("/api/v1/enterprise-analytics/dashboard")
        self.assertEqual(dashboard.status_code, 200)
        payload = dashboard.get_json()
        self.assertEqual(payload["phase"], "4.6")
        self.assertTrue(payload["read_only"])
        self.assertEqual(len(payload["features"]), 11)

    def test_executive_export_and_legacy_reporting(self):
        export = self.client.get("/api/v1/enterprise-analytics/export")
        self.assertEqual(export.status_code, 200)
        self.assertTrue(export.get_json()["read_only"])

        csv_export = self.client.get("/api/v1/enterprise-analytics/export?format=csv")
        self.assertEqual(csv_export.status_code, 200)

        legacy = self.client.get("/api/v1/reports/revenue")
        self.assertEqual(legacy.status_code, 200)


if __name__ == "__main__":
    unittest.main()
