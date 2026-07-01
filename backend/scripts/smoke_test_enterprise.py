import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.extensions.db import db
from app.services.enterprise_platform_service import EnterprisePlatformService


def smoke_test():
    with app.app_context():
        db.create_all()
        EnterprisePlatformService.ensure_defaults()
        steps = [
            ("GET admin overview", "get", "/api/v1/admin/overview", None),
            ("GET admin health", "get", "/api/v1/admin/health", None),
            ("GET admin metrics", "get", "/api/v1/admin/metrics", None),
            ("GET feature flags", "get", "/api/v1/admin/feature-flags", None),
            ("GET usage", "get", "/api/v1/admin/usage", None),
            ("GET tenants", "get", "/api/v1/tenants", None),
            ("GET licenses", "get", "/api/v1/licenses", None),
            ("GET rbac roles", "get", "/api/v1/security/rbac/roles", None),
            ("GET abac policies", "get", "/api/v1/security/abac/policies", None),
            ("GET identity providers", "get", "/api/v1/security/identity-providers", None),
            ("GET organizations", "get", "/api/v1/security/organizations", None),
            ("GET audit records", "get", "/api/v1/audit/records", None),
            ("POST audit record", "post", "/api/v1/audit/records", {"action": "SMOKE_TEST", "actor_email": "smoke@dxcon.local"}),
            ("POST compliance export", "post", "/api/v1/audit/compliance-export", {}),
            ("GET admin dashboard", "get", "/admin", None),
            ("GET security dashboard", "get", "/security", None),
            ("GET license dashboard", "get", "/license", None),
            ("GET tenants dashboard", "get", "/tenants", None),
            ("GET system dashboard", "get", "/system", None),
        ]
        tenant_id = None
        for label, method, path, payload in steps:
            if method == "get":
                response = client.get(path)
            else:
                response = client.post(path, json=payload or {})
            if response.status_code >= 400:
                print("FAIL:", label, response.status_code, response.get_data(as_text=True)[:200])
                return False
            if path == "/api/v1/tenants" and method == "get":
                tenants = response.get_json().get("tenants") or []
                if tenants:
                    tenant_id = tenants[0]["id"]
            print("OK:", label, response.status_code)
        if tenant_id:
            iso = client.get(f"/api/v1/tenants/{tenant_id}/isolation")
            if iso.status_code >= 400:
                print("FAIL: tenant isolation", iso.status_code)
                return False
            print("OK: tenant isolation", iso.status_code)
        return True


app = create_app()
app.config["TESTING"] = True
client = app.test_client()
print("\n=== DXCON ENTERPRISE SMOKE TEST ===\n")
if not smoke_test():
    print("\nENTERPRISE SMOKE TEST FAILED\n")
    sys.exit(1)
print("\nENTERPRISE SMOKE TEST PASSED\n")
