import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.extensions.db import db
from app.models.enterprise_platform import (
    EnterpriseAbacPolicy,
    EnterpriseAccessHistory,
    EnterpriseAuditRecord,
    EnterpriseBackgroundJob,
    EnterpriseBusinessUnit,
    EnterpriseComplianceExport,
    EnterpriseDepartment,
    EnterpriseFeatureFlag,
    EnterpriseIdentityProvider,
    EnterpriseLicense,
    EnterpriseOrganization,
    EnterpriseRole,
    EnterpriseSecurityEvent,
    EnterpriseSystemSetting,
    EnterpriseTenant,
    EnterpriseUsageMetric,
)
from app.services.enterprise_platform_service import (
    AdminEnterpriseService,
    AuditEnterpriseService,
    EnterprisePlatformService,
    LicenseEnterpriseService,
    MonitoringEnterpriseService,
    SecurityEnterpriseService,
    TenantEnterpriseService,
)


def verify_models_import():
    models = [
        EnterpriseTenant,
        EnterpriseOrganization,
        EnterpriseDepartment,
        EnterpriseBusinessUnit,
        EnterpriseRole,
        EnterpriseAbacPolicy,
        EnterpriseIdentityProvider,
        EnterpriseLicense,
        EnterpriseFeatureFlag,
        EnterpriseSystemSetting,
        EnterpriseAuditRecord,
        EnterpriseAccessHistory,
        EnterpriseSecurityEvent,
        EnterpriseComplianceExport,
        EnterpriseUsageMetric,
        EnterpriseBackgroundJob,
    ]
    for model in models:
        assert model.__tablename__
        print("OK: model", model.__name__)
    return True


def verify_routes(app):
    routes = {str(rule) for rule in app.url_map.iter_rules()}
    required_api = [
        "/api/v1/admin/overview",
        "/api/v1/admin/settings",
        "/api/v1/admin/feature-flags",
        "/api/v1/admin/usage",
        "/api/v1/admin/health",
        "/api/v1/admin/metrics",
        "/api/v1/admin/tracing",
        "/api/v1/admin/jobs",
        "/api/v1/tenants",
        "/api/v1/tenants/<tenant_id>",
        "/api/v1/tenants/<tenant_id>/isolation",
        "/api/v1/licenses",
        "/api/v1/licenses/<license_id>",
        "/api/v1/licenses/<license_id>/validate",
        "/api/v1/security/rbac/roles",
        "/api/v1/security/abac/policies",
        "/api/v1/security/abac/evaluate",
        "/api/v1/security/identity-providers",
        "/api/v1/security/organizations",
        "/api/v1/security/departments",
        "/api/v1/audit/records",
        "/api/v1/audit/access-history",
        "/api/v1/audit/security-events",
        "/api/v1/audit/compliance-export",
    ]
    required_web = ["/admin", "/security", "/license", "/tenants", "/system"]
    for route in required_api + required_web:
        if route in routes:
            print("OK:", route)
        else:
            print("MISSING:", route)
            return False
    return True


def verify_no_duplicate_routes(app):
    prefixes = ("/api/v1/admin/", "/api/v1/tenants", "/api/v1/licenses", "/api/v1/security/", "/api/v1/audit")
    seen = set()
    for rule in app.url_map.iter_rules():
        path = str(rule.rule)
        if not any(path.startswith(prefix) or path == prefix.rstrip("/") for prefix in prefixes):
            if path not in {"/admin", "/security", "/license", "/tenants", "/system"}:
                continue
        key = (path, tuple(sorted(rule.methods)))
        if key in seen:
            print("DUPLICATE:", key)
            return False
        seen.add(key)
    print("OK: no duplicate enterprise routes")
    return True


def verify_engines():
    with app.app_context():
        db.create_all()
        seed = EnterprisePlatformService.ensure_defaults()
        if not seed.get("seeded") and EnterpriseTenant.query.count() < 1:
            print("MISSING: enterprise seed")
            return False
        print("OK: enterprise seed")

        tenants = TenantEnterpriseService.list_tenants()
        if tenants["count"] < 1:
            print("MISSING: tenants")
            return False
        isolation = TenantEnterpriseService.isolation(tenants["tenants"][0]["id"])
        if not isolation["isolated"]:
            print("MISSING: tenant isolation")
            return False
        print("OK: multi-tenant isolation")

        rbac = SecurityEnterpriseService.list_rbac_roles()
        abac = SecurityEnterpriseService.list_abac_policies()
        if rbac["count"] < 1 or abac["count"] < 1:
            print("MISSING: RBAC/ABAC")
            return False
        print("OK: RBAC and ABAC")

        idp = SecurityEnterpriseService.list_identity_providers()
        if idp["count"] < 3:
            print("MISSING: identity providers")
            return False
        print("OK: OIDC/OAuth2/SAML providers")

        license_row = LicenseEnterpriseService.list_licenses()["licenses"][0]
        valid = LicenseEnterpriseService.validate(license_row["id"])
        if not valid["valid"]:
            print("MISSING: license validation")
            return False
        print("OK: license management")

        flags = AdminEnterpriseService.list_feature_flags()
        settings = AdminEnterpriseService.list_settings()
        usage = AdminEnterpriseService.usage_statistics()
        if flags["count"] < 1 or settings["count"] < 1 or usage["count"] < 1:
            print("MISSING: administration features")
            return False
        print("OK: feature flags, settings, usage")

        record = AuditEnterpriseService.append_record(action="VERIFY", actor_email="verify@dxcon.local")
        if not record.get("immutable"):
            print("MISSING: immutable audit")
            return False
        AuditEnterpriseService.log_access({"user_email": "u@dxcon.local", "resource": "/admin", "action": "GET"})
        AuditEnterpriseService.log_security_event({"event_type": "LOGIN", "message": "verify"})
        export = AuditEnterpriseService.compliance_export({})
        if EnterpriseAccessHistory.query.count() < 1 or EnterpriseSecurityEvent.query.count() < 1:
            print("MISSING: access history or security events")
            return False
        if not export.get("export_code"):
            print("MISSING: compliance export")
            return False
        print("OK: audit, access history, security events, compliance export")

        health = MonitoringEnterpriseService.health()
        metrics = MonitoringEnterpriseService.metrics()
        jobs = MonitoringEnterpriseService.background_jobs()
        if health["status"] != "OK" or not metrics or jobs["count"] < 1:
            print("MISSING: monitoring")
            return False
        print("OK: health, metrics, background jobs")
        return True


app = create_app()
print("\n=== DXCON ENTERPRISE VERIFY ===\n")
errors = 0
if not verify_models_import():
    errors += 1
if not verify_routes(app):
    errors += 1
if not verify_no_duplicate_routes(app):
    errors += 1
if not verify_engines():
    errors += 1
if errors:
    print("\nFAILED:", errors, "issue(s)")
    sys.exit(1)
print("\nENTERPRISE VERIFY PASSED\n")
