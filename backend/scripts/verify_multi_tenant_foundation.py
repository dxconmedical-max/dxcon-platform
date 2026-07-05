#!/usr/bin/env python3
"""Verify Multi Tenant Foundation Phase 7.1."""

from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
REPORT_PATH = ROOT / "generated_release" / "MULTI_TENANT_FOUNDATION_REPORT.json"
ARCH_DOC = REPO / "docs" / "architecture" / "TENANT_ARCHITECTURE.md"

WEB_ROUTES = (
    "/multi-tenant",
    "/multi-tenant/tenants",
    "/multi-tenant/organizations",
    "/multi-tenant/clinics",
    "/multi-tenant/laboratories",
    "/multi-tenant/settings",
    "/multi-tenant/resolver",
    "/multi-tenant/context",
    "/multi-tenant/middleware",
    "/multi-tenant/admin",
    "/multi-tenant/audit",
    "/multi-tenant/isolation",
)

API_ROUTES = (
    "/api/v1/multi-tenant/dashboard",
    "/api/v1/multi-tenant/tenants",
    "/api/v1/multi-tenant/organizations",
    "/api/v1/multi-tenant/clinics",
    "/api/v1/multi-tenant/laboratories",
    "/api/v1/multi-tenant/settings",
    "/api/v1/multi-tenant/resolver",
    "/api/v1/multi-tenant/context",
    "/api/v1/multi-tenant/middleware",
    "/api/v1/multi-tenant/admin",
    "/api/v1/multi-tenant/audit",
    "/api/v1/multi-tenant/isolation",
    "/api/v1/multi-tenant/readiness",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _login_admin(client):
    from app.models.user import User

    user = User.query.filter(User.role == "SUPER_ADMIN").first()
    if not user:
        user = User.query.filter(User.role == "ADMIN").first()
    if not user:
        return False
    with client.session_transaction() as sess:
        sess["user_id"] = user.id
        sess["role"] = user.role
        sess["email"] = user.email
    return True


def _api_json(response):
    payload = response.get_json() or {}
    if isinstance(payload, dict) and payload.get("success") is True and "data" in payload:
        return payload["data"]
    return payload


def main() -> int:
    sys.path.insert(0, str(ROOT))
    if not os.getenv("DATABASE_URL"):
        print("FAIL: DATABASE_URL is required", file=sys.stderr)
        return 1

    print("\n=== DXCON MULTI TENANT FOUNDATION VERIFY ===\n")
    start = time.perf_counter()
    checks: dict[str, dict] = {}

    from app import create_app

    app = create_app()
    with app.app_context():
        from app.core.passwords import hash_password
        from app.extensions.db import db
        from app.models.user import User
        from app.services.multi_tenant_foundation_service import FEATURES, ensure_multi_tenant_foundation

        db.create_all()
        if not User.query.filter(User.role.in_(("SUPER_ADMIN", "ADMIN"))).first():
            db.session.add(
                User(
                    email="verify-multi-tenant@demo.dxcon.test",
                    role="ADMIN",
                    password_hash=hash_password("DemoPass123!"),
                    is_active=True,
                )
            )
            db.session.commit()

        ensure_multi_tenant_foundation()

        routes = {str(rule.rule) for rule in app.url_map.iter_rules()}
        missing_web = [route for route in WEB_ROUTES if route not in routes]
        missing_api = [route for route in API_ROUTES if route not in routes]
        checks["route_registry"] = {
            "ok": not missing_web and not missing_api,
            "missing_web": missing_web,
            "missing_api": missing_api,
        }

        checks["architecture_doc"] = {"ok": ARCH_DOC.exists(), "path": str(ARCH_DOC.relative_to(REPO))}

        client = app.test_client()
        checks["auth"] = {"ok": _login_admin(client)}

        web_ok = True
        web_results = {}
        for route in WEB_ROUTES:
            response = client.get(route, follow_redirects=True)
            ok = response.status_code == 200 and len(response.get_data(as_text=True)) > 200
            web_ok = web_ok and ok
            web_results[route] = {"status_code": response.status_code, "ok": ok}
        checks["web_pages"] = {"ok": web_ok, "routes": web_results}

        api_ok = True
        api_results = {}
        for route in API_ROUTES:
            response = client.get(route, follow_redirects=True)
            ok = response.status_code == 200
            api_ok = api_ok and ok
            api_results[route] = {"status_code": response.status_code, "ok": ok}
        checks["api_endpoints"] = {"ok": api_ok, "routes": api_results}

        dashboard = _api_json(client.get("/api/v1/multi-tenant/dashboard"))
        checks["feature_coverage"] = {
            "ok": len(dashboard.get("features", [])) == 11 and list(FEATURES) == dashboard.get("features"),
            "features": len(FEATURES),
        }

        checks["tenant_registry"] = {
            "ok": _api_json(client.get("/api/v1/multi-tenant/tenants")).get("report") == "tenant_registry",
        }
        checks["organization_registry"] = {
            "ok": _api_json(client.get("/api/v1/multi-tenant/organizations")).get("report") == "organization_registry",
        }
        checks["clinic_registry"] = {
            "ok": "clinics" in _api_json(client.get("/api/v1/multi-tenant/clinics")),
        }
        checks["laboratory_registry"] = {
            "ok": "laboratories" in _api_json(client.get("/api/v1/multi-tenant/laboratories")),
        }
        checks["organization_settings"] = {
            "ok": _api_json(client.get("/api/v1/multi-tenant/settings")).get("report") == "organization_settings",
        }
        checks["tenant_resolver"] = {
            "ok": _api_json(client.get("/api/v1/multi-tenant/resolver")).get("resolver") == "TenantResolver",
        }
        checks["tenant_context"] = {
            "ok": "context_fields" in _api_json(client.get("/api/v1/multi-tenant/context")),
        }
        checks["tenant_middleware"] = {
            "ok": _api_json(client.get("/api/v1/multi-tenant/middleware")).get("registered") is True,
        }
        checks["tenant_admin"] = {
            "ok": _api_json(client.get("/api/v1/multi-tenant/admin")).get("report") == "tenant_admin",
        }
        checks["tenant_audit"] = {
            "ok": "records" in _api_json(client.get("/api/v1/multi-tenant/audit")),
        }
        checks["tenant_isolation"] = {
            "ok": _api_json(client.get("/api/v1/multi-tenant/isolation")).get("report") == "tenant_isolation_framework",
        }

        legacy = client.get("/tenant-isolation", follow_redirects=True)
        checks["legacy_tenant_isolation_preserved"] = {"ok": legacy.status_code == 200}

        legacy_api = client.get("/api/v1/tenant-isolation/dashboard", follow_redirects=True)
        checks["legacy_tenant_isolation_api_preserved"] = {"ok": legacy_api.status_code == 200}

        legacy_tenants = client.get("/api/v1/tenants", follow_redirects=True)
        checks["legacy_tenants_api_preserved"] = {"ok": legacy_tenants.status_code == 200}

    passed = sum(1 for item in checks.values() if item.get("ok"))
    total = len(checks)
    score = round((passed / total) * 100, 1) if total else 0.0
    report = {
        "generated_at": utc_now(),
        "phase": "7.1",
        "sprint": "Multi Tenant Foundation",
        "summary": {
            "score": score,
            "checks_passed": passed,
            "checks_total": total,
            "ok": passed == total,
            "runtime_seconds": round(time.perf_counter() - start, 3),
        },
        "checks": checks,
    }
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")

    print(f"Multi Tenant Foundation score: {score}%")
    print(f"Checks passed: {passed}/{total}")
    print(f"Report: {REPORT_PATH}")
    if report["summary"]["ok"]:
        print("MULTI TENANT FOUNDATION VERIFY PASS\n")
        return 0
    print("MULTI TENANT FOUNDATION VERIFY FAIL\n")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
