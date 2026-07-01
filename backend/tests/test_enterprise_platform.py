import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.core.statuses import (
    ENTERPRISE_IDENTITY_OIDC,
    ENTERPRISE_IDENTITY_SAML,
    ENTERPRISE_LICENSE_ACTIVE,
)
from app.extensions.db import db
from app.models.enterprise_platform import (
    EnterpriseAuditRecord,
    EnterpriseFeatureFlag,
    EnterpriseLicense,
    EnterpriseTenant,
)
from app.services.enterprise_platform_service import (
    AuditEnterpriseService,
    EnterprisePlatformService,
    SecurityEnterpriseService,
    TenantEnterpriseService,
)


class EnterprisePlatformTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()
        EnterprisePlatformService.ensure_defaults()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def test_admin_api(self):
        overview = self.client.get("/api/v1/admin/overview")
        self.assertEqual(overview.status_code, 200)
        self.assertGreaterEqual(overview.get_json()["tenants"], 1)

        health = self.client.get("/api/v1/admin/health")
        self.assertEqual(health.status_code, 200)
        self.assertEqual(health.get_json()["status"], "OK")

        metrics = self.client.get("/api/v1/admin/metrics")
        self.assertEqual(metrics.status_code, 200)

        flags = self.client.get("/api/v1/admin/feature-flags")
        self.assertEqual(flags.status_code, 200)
        self.assertGreaterEqual(flags.get_json()["count"], 1)

    def test_tenants_api(self):
        response = self.client.get("/api/v1/tenants")
        self.assertEqual(response.status_code, 200)
        tenant_id = response.get_json()["tenants"][0]["id"]

        isolation = self.client.get(f"/api/v1/tenants/{tenant_id}/isolation")
        self.assertEqual(isolation.status_code, 200)
        self.assertTrue(isolation.get_json()["isolated"])

        create = self.client.post("/api/v1/tenants", json={"name": "Partner Tenant"})
        self.assertEqual(create.status_code, 201)

    def test_licenses_api(self):
        licenses = self.client.get("/api/v1/licenses")
        self.assertEqual(licenses.status_code, 200)
        license_id = licenses.get_json()["licenses"][0]["id"]

        validate = self.client.post(f"/api/v1/licenses/{license_id}/validate")
        self.assertEqual(validate.status_code, 200)
        self.assertTrue(validate.get_json()["valid"])

    def test_security_api(self):
        rbac = self.client.get("/api/v1/security/rbac/roles")
        self.assertEqual(rbac.status_code, 200)
        self.assertGreaterEqual(rbac.get_json()["count"], 1)

        abac = self.client.get("/api/v1/security/abac/policies")
        self.assertEqual(abac.status_code, 200)

        evaluate = self.client.post(
            "/api/v1/security/abac/evaluate",
            json={"resource": "lab_result", "action": "read", "context": {"department": "DEPT-LIS", "tenant_id": "t1"}},
        )
        self.assertEqual(evaluate.status_code, 200)
        self.assertEqual(evaluate.get_json()["effect"], "ALLOW")

        idp = self.client.get("/api/v1/security/identity-providers")
        self.assertEqual(idp.status_code, 200)
        types = {row["provider_type"] for row in idp.get_json()["providers"]}
        self.assertIn(ENTERPRISE_IDENTITY_OIDC, types)
        self.assertIn(ENTERPRISE_IDENTITY_SAML, types)

        orgs = self.client.get("/api/v1/security/organizations")
        self.assertEqual(orgs.status_code, 200)
        depts = self.client.get("/api/v1/security/departments")
        self.assertEqual(depts.status_code, 200)

    def test_audit_api(self):
        append = self.client.post(
            "/api/v1/audit/records",
            json={"action": "TEST_ACTION", "actor_email": "admin@dxcon.local", "payload": {"test": True}},
        )
        self.assertEqual(append.status_code, 201)
        self.assertTrue(append.get_json()["immutable"])

        records = self.client.get("/api/v1/audit/records")
        self.assertEqual(records.status_code, 200)
        self.assertGreaterEqual(records.get_json()["count"], 1)

        access = self.client.post(
            "/api/v1/audit/access-history",
            json={"user_email": "user@dxcon.local", "resource": "/api/v1/admin", "action": "GET"},
        )
        self.assertEqual(access.status_code, 201)

        event = self.client.post(
            "/api/v1/audit/security-events",
            json={"event_type": "LOGIN", "message": "Successful login"},
        )
        self.assertEqual(event.status_code, 201)

        export = self.client.post("/api/v1/audit/compliance-export", json={"export_type": "AUDIT"})
        self.assertEqual(export.status_code, 201)

    def test_dashboard_pages(self):
        for path in ("/admin", "/security", "/license", "/tenants", "/system"):
            response = self.client.get(path)
            self.assertEqual(response.status_code, 200, path)

    def test_services(self):
        self.assertGreaterEqual(EnterpriseTenant.query.count(), 1)
        self.assertGreaterEqual(EnterpriseLicense.query.filter_by(status=ENTERPRISE_LICENSE_ACTIVE).count(), 1)
        self.assertGreaterEqual(EnterpriseFeatureFlag.query.count(), 1)
        self.assertGreaterEqual(EnterpriseAuditRecord.query.count(), 1)
        tenant = TenantEnterpriseService.list_tenants()["tenants"][0]
        isolation = TenantEnterpriseService.isolation(tenant["id"])
        self.assertTrue(isolation["isolated"])
        abac = SecurityEnterpriseService.evaluate_abac(
            {"resource": "lab_result", "action": "read", "context": {"department": "DEPT-LIS", "tenant_id": "x"}}
        )
        self.assertEqual(abac["effect"], "ALLOW")
        record = AuditEnterpriseService.append_record(action="SERVICE_TEST", actor_email="test@dxcon.local")
        self.assertTrue(record["immutable"])


if __name__ == "__main__":
    unittest.main()
