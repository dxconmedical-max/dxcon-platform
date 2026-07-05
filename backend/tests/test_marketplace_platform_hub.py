import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"


class MarketplacePlatformTestCase(unittest.TestCase):
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
            email="demo-admin-mp@demo.dxcon.test",
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

    def test_marketplace_platform_routes_registered(self):
        routes = {str(rule.rule) for rule in self.app.url_map.iter_rules()}
        for route in (
            "/marketplace-platform",
            "/marketplace-platform/health",
            "/api/v1/marketplace-platform/dashboard",
            "/api/v1/marketplace-platform/readiness",
        ):
            self.assertIn(route, routes)

    def test_dashboard_and_plugin_sections(self):
        response = self.client.get("/marketplace-platform")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Marketplace Platform", response.get_data(as_text=True))

        dashboard = self.client.get("/api/v1/marketplace-platform/dashboard")
        self.assertEqual(dashboard.status_code, 200)
        payload = dashboard.get_json()
        self.assertEqual(payload["phase"], "7.2")
        self.assertEqual(len(payload["features"]), 9)

        health = self.client.get("/api/v1/marketplace-platform/health")
        self.assertIn("checks", health.get_json())

    def test_legacy_marketplace_preserved(self):
        legacy = self.client.get("/marketplace")
        self.assertEqual(legacy.status_code, 200)
        plugins = self.client.get("/api/v1/plugins")
        self.assertEqual(plugins.status_code, 200)


if __name__ == "__main__":
    unittest.main()
