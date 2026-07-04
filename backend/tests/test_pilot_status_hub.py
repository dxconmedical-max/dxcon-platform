import os
import sys
import unittest
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"


class PilotStatusTestCase(unittest.TestCase):
    def setUp(self):
        from app import create_app
        from app.core.passwords import hash_password
        from app.extensions.db import db
        from app.models.alert import Alert
        from app.models.clinic_profile import ClinicProfile
        from app.models.driver import Driver
        from app.models.laboratory import Laboratory
        from app.models.order import Order
        from app.models.user import User

        self.app = create_app()
        self.app.config["TESTING"] = True
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()
        db.session.add(
            ClinicProfile(
                clinic_id=str(uuid.uuid4()),
                clinic_code="TEST-CLN-001",
                name="Test Clinic",
                status="ACTIVE",
            )
        )
        db.session.add(Laboratory(code="TEST-LAB-001", name="Test Lab", is_active=True))
        db.session.add(
            Driver(
                driver_code="TEST-COL-001",
                full_name="Test Collector",
                status="ACTIVE",
            )
        )
        db.session.add(
            Order(
                order_code="TEST-ORD-001",
                patient_id=str(uuid.uuid4()),
                status="PENDING",
                total_amount=100000,
            )
        )
        db.session.add(
            Alert(
                alert_code="TEST-ALR-001",
                alert_type="OPERATIONS",
                severity="LOW",
                message="Test alert",
                status="OPEN",
            )
        )
        user = User(
            email="demo-admin-pilot@demo.dxcon.test",
            role="ADMIN",
            password_hash=hash_password("DemoPass123!"),
            is_active=True,
        )
        db.session.add(user)
        db.session.commit()
        self.client = self.app.test_client()
        with self.client.session_transaction() as sess:
            sess["user_id"] = user.id
            sess["role"] = user.role
            sess["email"] = user.email

    def tearDown(self):
        from app.extensions.db import db

        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def test_pilot_status_routes_registered(self):
        routes = {str(rule.rule) for rule in self.app.url_map.iter_rules()}
        for route in (
            "/pilot-status",
            "/pilot-status/alerts",
            "/api/v1/pilot-status/dashboard",
            "/api/v1/pilot-status/readiness",
        ):
            self.assertIn(route, routes)

    def test_dashboard_and_overview(self):
        response = self.client.get("/pilot-status")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Pilot Status", response.get_data(as_text=True))

        dashboard = self.client.get("/api/v1/pilot-status/dashboard")
        self.assertEqual(dashboard.status_code, 200)
        payload = dashboard.get_json()
        self.assertEqual(payload["phase"], "5.6")
        self.assertEqual(len(payload["features"]), 8)

        overview = self.client.get("/api/v1/pilot-status/overview")
        self.assertEqual(overview.status_code, 200)
        self.assertGreaterEqual(overview.get_json()["summary"]["active_clinics"], 1)

    def test_legacy_dashboard_preserved(self):
        summary = self.client.get("/api/v1/dashboard/summary")
        self.assertEqual(summary.status_code, 200)
        payload = summary.get_json()
        if payload.get("success"):
            payload = payload["data"]
        self.assertIn("orders", payload)


if __name__ == "__main__":
    unittest.main()
