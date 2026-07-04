import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"


class MonitoringCenterTestCase(unittest.TestCase):
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
            email="demo-admin-monitoring@demo.dxcon.test",
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

    def test_monitoring_center_routes_registered(self):
        routes = {str(rule.rule) for rule in self.app.url_map.iter_rules()}
        for route in (
            "/monitoring",
            "/monitoring/alerts",
            "/api/v1/monitoring-center/dashboard",
            "/api/v1/monitoring-center/readiness",
        ):
            self.assertIn(route, routes)

    def test_dashboard_and_readiness(self):
        response = self.client.get("/monitoring")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Monitoring Center", response.get_data(as_text=True))

        dashboard = self.client.get("/api/v1/monitoring-center/dashboard")
        self.assertEqual(dashboard.status_code, 200)
        payload = dashboard.get_json()
        self.assertEqual(payload["phase"], "5.2")
        self.assertEqual(len(payload["features"]), 9)

        readiness = self.client.get("/api/v1/monitoring-center/readiness")
        self.assertEqual(readiness.status_code, 200)
        self.assertIn("sections", readiness.get_json())

    def test_legacy_monitoring_preserved(self):
        monitor = self.client.get("/monitor")
        self.assertEqual(monitor.status_code, 200)
        health = self.client.get("/api/v1/system/health")
        self.assertEqual(health.status_code, 200)


if __name__ == "__main__":
    unittest.main()
