import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"


class PilotToolkitTestCase(unittest.TestCase):
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
            email="demo-admin-pilot-toolkit@demo.dxcon.test",
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

    def test_pilot_toolkit_routes_registered(self):
        routes = {str(rule.rule) for rule in self.app.url_map.iter_rules()}
        for route in (
            "/pilot-toolkit",
            "/pilot-toolkit/reports",
            "/api/v1/pilot-toolkit/dashboard",
            "/api/v1/pilot-toolkit/readiness",
        ):
            self.assertIn(route, routes)

    def test_dashboard_and_sections(self):
        response = self.client.get("/pilot-toolkit")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Pilot Toolkit", response.get_data(as_text=True))

        dashboard = self.client.get("/api/v1/pilot-toolkit/dashboard")
        self.assertEqual(dashboard.status_code, 200)
        payload = dashboard.get_json()
        self.assertEqual(payload["phase"], "5.13")
        self.assertEqual(len(payload["features"]), 8)

        workflow = self.client.get("/api/v1/pilot-toolkit/workflow")
        self.assertGreaterEqual(workflow.get_json().get("steps_total", 0), 8)

    def test_legacy_pilot_pages_preserved(self):
        demo = self.client.get("/demo-accounts")
        self.assertEqual(demo.status_code, 200)
        workflow = self.client.get("/workflow-demo")
        self.assertEqual(workflow.status_code, 200)
        reports = self.client.get("/reports")
        self.assertEqual(reports.status_code, 200)


if __name__ == "__main__":
    unittest.main()
