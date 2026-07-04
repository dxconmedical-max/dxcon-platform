import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"


class TenantIsolationTestCase(unittest.TestCase):
    def setUp(self):
        from app import create_app
        from app.core.passwords import hash_password
        from app.extensions.db import db
        from app.models.user import User
        from app.services.tenant_isolation_service import ensure_demo_clinics

        self.app = create_app()
        self.app.config["TESTING"] = True
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()
        ensure_demo_clinics()
        self.client = self.app.test_client()
        user = User(
            email="demo-admin-tenant@demo.dxcon.test",
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

    def test_tenant_isolation_routes_registered(self):
        routes = {str(rule.rule) for rule in self.app.url_map.iter_rules()}
        for route in (
            "/tenant-isolation",
            "/tenant-isolation/isolation",
            "/api/v1/tenant-isolation/dashboard",
            "/api/v1/tenant-isolation/readiness",
        ):
            self.assertIn(route, routes)

    def test_platform_and_clinics(self):
        response = self.client.get("/tenant-isolation")
        self.assertEqual(response.status_code, 200)
        self.assertIn("One Platform", response.get_data(as_text=True))

        dashboard = self.client.get("/api/v1/tenant-isolation/dashboard")
        self.assertEqual(dashboard.status_code, 200)
        payload = dashboard.get_json()
        self.assertEqual(payload["phase"], "5.4")
        self.assertEqual(len(payload["features"]), 5)

        clinic_a = self.client.get("/api/v1/tenant-isolation/clinic-a")
        self.assertEqual(clinic_a.get_json()["label"], "Clinic A")

    def test_legacy_tenants_preserved(self):
        tenants = self.client.get("/api/v1/tenants")
        self.assertEqual(tenants.status_code, 200)
        data = tenants.get_json()
        if data.get("success"):
            data = data["data"]
        self.assertGreaterEqual(data["count"], 3)


if __name__ == "__main__":
    unittest.main()
