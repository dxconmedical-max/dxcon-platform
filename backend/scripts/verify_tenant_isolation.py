#!/usr/bin/env python3
"""Verify Tenant Isolation Phase 5 Sprint 5.4."""

from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = ROOT / "generated_release" / "TENANT_ISOLATION_REPORT.json"

WEB_ROUTES = (
    "/tenant-isolation",
    "/tenant-isolation/clinic-a",
    "/tenant-isolation/clinic-b",
    "/tenant-isolation/clinic-c",
    "/tenant-isolation/isolation",
)

API_ROUTES = (
    "/api/v1/tenant-isolation/dashboard",
    "/api/v1/tenant-isolation/platform",
    "/api/v1/tenant-isolation/clinic-a",
    "/api/v1/tenant-isolation/clinic-b",
    "/api/v1/tenant-isolation/clinic-c",
    "/api/v1/tenant-isolation/isolation",
    "/api/v1/tenant-isolation/inventory",
    "/api/v1/tenant-isolation/readiness",
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

    print("\n=== DXCON TENANT ISOLATION VERIFY ===\n")
    start = time.perf_counter()
    checks: dict[str, dict] = {}

    from app import create_app

    app = create_app()
    with app.app_context():
        from app.core.passwords import hash_password
        from app.extensions.db import db
        from app.models.user import User
        from app.services.tenant_isolation_service import FEATURES, ensure_demo_clinics

        db.create_all()
        if not User.query.filter(User.role.in_(("SUPER_ADMIN", "ADMIN"))).first():
            db.session.add(
                User(
                    email="verify-tenant@demo.dxcon.test",
                    role="ADMIN",
                    password_hash=hash_password("DemoPass123!"),
                    is_active=True,
                )
            )
            db.session.commit()

        ensure_demo_clinics()

        routes = {str(rule.rule) for rule in app.url_map.iter_rules()}
        missing_web = [route for route in WEB_ROUTES if route not in routes]
        missing_api = [route for route in API_ROUTES if route not in routes]
        checks["route_registry"] = {
            "ok": not missing_web and not missing_api,
            "missing_web": missing_web,
            "missing_api": missing_api,
        }

        client = app.test_client()
        if not _login_admin(client):
            checks["auth"] = {"ok": False, "reason": "no admin user"}
        else:
            checks["auth"] = {"ok": True}

        web_ok = True
        web_results = {}
        for route in WEB_ROUTES:
            response = client.get(route, follow_redirects=True)
            ok = response.status_code == 200 and len(response.get_data(as_text=True)) > 200
            web_ok = web_ok and ok
            web_results[route] = {"status_code": response.status_code, "ok": ok}
        checks["one_platform"] = {"ok": web_ok, "routes": web_results}

        api_ok = True
        api_results = {}
        for route in API_ROUTES:
            response = client.get(route, follow_redirects=True)
            ok = response.status_code == 200
            api_ok = api_ok and ok
            api_results[route] = {"status_code": response.status_code, "ok": ok}
        checks["api_endpoints"] = {"ok": api_ok, "routes": api_results}

        dashboard = _api_json(client.get("/api/v1/tenant-isolation/dashboard"))
        checks["feature_coverage"] = {
            "ok": len(dashboard.get("features", [])) == 5 and list(FEATURES) == dashboard.get("features"),
            "features": len(FEATURES),
        }

        checks["clinic_a"] = {
            "ok": _api_json(client.get("/api/v1/tenant-isolation/clinic-a")).get("label") == "Clinic A",
        }
        checks["clinic_b"] = {
            "ok": _api_json(client.get("/api/v1/tenant-isolation/clinic-b")).get("label") == "Clinic B",
        }
        checks["clinic_c"] = {
            "ok": _api_json(client.get("/api/v1/tenant-isolation/clinic-c")).get("label") == "Clinic C",
        }
        platform = _api_json(client.get("/api/v1/tenant-isolation/platform"))
        checks["one_platform_api"] = {
            "ok": len(platform.get("demo_clinics", [])) >= 3,
        }
        isolation = _api_json(client.get("/api/v1/tenant-isolation/isolation"))
        checks["tenant_isolation"] = {
            "ok": isolation.get("checks_passed", 0) >= 4,
        }

        tenants = _api_json(client.get("/api/v1/tenants"))
        checks["legacy_tenants_api_preserved"] = {
            "ok": tenants.get("count", 0) >= 3,
        }

        tenant_id = tenants.get("tenants", [{}])[0].get("id")
        legacy_iso = _api_json(client.get(f"/api/v1/tenants/{tenant_id}/isolation"))
        checks["legacy_isolation_api_preserved"] = {
            "ok": legacy_iso.get("isolated") is True,
        }

        legacy_web = client.get("/tenants")
        checks["legacy_tenants_web_preserved"] = {"ok": legacy_web.status_code == 200}

    passed = sum(1 for item in checks.values() if item.get("ok"))
    total = len(checks)
    score = round((passed / total) * 100, 1) if total else 0.0
    report = {
        "generated_at": utc_now(),
        "phase": "5.4",
        "sprint": "Tenant Isolation",
        "summary": {
            "score": score,
            "checks_passed": passed,
            "checks_total": total,
            "ok": passed == total,
            "runtime_seconds": round(time.perf_counter() - start, 3),
        },
        "checks": checks,
        "readiness": _api_json(client.get("/api/v1/tenant-isolation/readiness")) if "client" in locals() else {},
    }
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")

    print(f"Tenant Isolation score: {score}%")
    print(f"Checks passed: {passed}/{total}")
    print(f"Report: {REPORT_PATH}")
    if report["summary"]["ok"]:
        print("TENANT ISOLATION VERIFY PASS\n")
        return 0
    print("TENANT ISOLATION VERIFY FAIL\n")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
