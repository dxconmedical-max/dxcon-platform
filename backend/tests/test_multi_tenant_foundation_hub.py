import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"


class MultiTenantFoundationTestCase(unittest.TestCase):
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
            email="demo-admin-mtf@demo.dxcon.test",
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

    def test_multi_tenant_routes_registered(self):
        routes = {str(rule.rule) for rule in self.app.url_map.iter_rules()}
        for route in (
            "/multi-tenant",
            "/multi-tenant/isolation",
            "/api/v1/multi-tenant/dashboard",
            "/api/v1/multi-tenant/readiness",
        ):
            self.assertIn(route, routes)

    def test_dashboard_and_sections(self):
        response = self.client.get("/multi-tenant")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Multi Tenant Foundation", response.get_data(as_text=True))

        dashboard = self.client.get("/api/v1/multi-tenant/dashboard")
        self.assertEqual(dashboard.status_code, 200)
        payload = dashboard.get_json()
        self.assertEqual(payload["phase"], "7.1")
        self.assertEqual(len(payload["features"]), 11)

        resolver = self.client.get("/api/v1/multi-tenant/resolver")
        self.assertEqual(resolver.get_json()["resolver"], "TenantResolver")

    def test_tenant_resolver_with_header(self):
        from app.services.multi_tenant_foundation_service import ensure_multi_tenant_foundation
        from app.models.enterprise_platform import EnterpriseTenant

        ensure_multi_tenant_foundation()
        tenant = EnterpriseTenant.query.first()
        self.assertIsNotNone(tenant)
        response = self.client.get(
            "/api/v1/multi-tenant/dashboard",
            headers={"X-Tenant-ID": tenant.tenant_code},
        )
        self.assertEqual(response.status_code, 200)

    def test_legacy_tenant_isolation_preserved(self):
        legacy = self.client.get("/tenant-isolation")
        self.assertEqual(legacy.status_code, 200)
        legacy_api = self.client.get("/api/v1/tenant-isolation/dashboard")
        self.assertEqual(legacy_api.status_code, 200)


if __name__ == "__main__":
    unittest.main()
