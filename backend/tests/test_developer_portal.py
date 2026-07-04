import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"


class DeveloperPortalTestCase(unittest.TestCase):
    def setUp(self):
        from app import create_app
        from app.extensions.db import db
        from app.services.api_platform_service import ApiClientService

        self.app = create_app()
        self.app.config["TESTING"] = True
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()
        ApiClientService.ensure_defaults()
        self.client = self.app.test_client()

    def tearDown(self):
        from app.extensions.db import db

        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def test_developer_portal_routes_registered(self):
        routes = {str(rule.rule) for rule in self.app.url_map.iter_rules()}
        for route in (
            "/developer",
            "/developer/api",
            "/developer/webhooks",
            "/developer/sandbox",
            "/developer/onboarding",
            "/api/v1/developer-portal/dashboard",
            "/api/v1/developer-portal/status",
        ):
            self.assertIn(route, routes)

    def test_landing_and_docs_pages(self):
        landing = self.client.get("/developer")
        self.assertEqual(landing.status_code, 200)
        self.assertIn("Partner Developer Portal", landing.get_data(as_text=True))

        api_page = self.client.get("/developer/api")
        self.assertEqual(api_page.status_code, 200)
        self.assertIn("API Documentation", api_page.get_data(as_text=True))

    def test_dashboard_api_and_sandbox(self):
        dashboard = self.client.get("/api/v1/developer-portal/dashboard")
        self.assertEqual(dashboard.status_code, 200)
        payload = dashboard.get_json()
        self.assertEqual(payload["phase"], "4.5")
        self.assertEqual(len(payload["features"]), 10)

        sandbox = self.client.post(
            "/api/v1/developer-portal/sandbox/request",
            json={"method": "GET", "path": "/api/v1/api-platform/health"},
        )
        self.assertEqual(sandbox.status_code, 200)
        self.assertEqual(sandbox.get_json()["status_code"], 200)

    def test_legacy_developer_routes_preserved(self):
        for path in ("/developer/api-keys", "/developer/routes", "/api-docs"):
            response = self.client.get(path)
            self.assertEqual(response.status_code, 200, path)


if __name__ == "__main__":
    unittest.main()
