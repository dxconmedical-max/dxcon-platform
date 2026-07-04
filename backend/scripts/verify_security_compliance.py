#!/usr/bin/env python3
"""Verify Security & Compliance Phase 5 Sprint 5.1."""

from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = ROOT / "generated_release" / "SECURITY_READINESS_REPORT.json"

WEB_ROUTES = (
    "/security-compliance",
    "/security-compliance/secrets",
    "/security-compliance/api-keys",
    "/security-compliance/jwt",
    "/security-compliance/rbac",
    "/security-compliance/audit",
    "/security-compliance/timeline",
    "/security-compliance/failed-logins",
    "/security-compliance/ip-whitelist",
    "/security-compliance/rate-limits",
    "/security-compliance/phi-access",
    "/security-compliance/compliance",
)

API_ROUTES = (
    "/api/v1/security-compliance/dashboard",
    "/api/v1/security-compliance/secrets",
    "/api/v1/security-compliance/api-keys",
    "/api/v1/security-compliance/jwt",
    "/api/v1/security-compliance/rbac",
    "/api/v1/security-compliance/audit",
    "/api/v1/security-compliance/timeline",
    "/api/v1/security-compliance/failed-logins",
    "/api/v1/security-compliance/ip-whitelist",
    "/api/v1/security-compliance/rate-limits",
    "/api/v1/security-compliance/phi-access",
    "/api/v1/security-compliance/compliance",
    "/api/v1/security-compliance/readiness",
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

    print("\n=== DXCON SECURITY & COMPLIANCE VERIFY ===\n")
    start = time.perf_counter()
    checks: dict[str, dict] = {}

    from app import create_app

    app = create_app()
    with app.app_context():
        from app.core.passwords import hash_password
        from app.extensions.db import db
        from app.models.user import User
        from app.services.api_platform_service import ApiClientService
        from app.services.enterprise_platform_service import EnterprisePlatformService

        db.create_all()
        if not User.query.filter(User.role.in_(("SUPER_ADMIN", "ADMIN"))).first():
            db.session.add(
                User(
                    email="verify-security@demo.dxcon.test",
                    role="ADMIN",
                    password_hash=hash_password("DemoPass123!"),
                    is_active=True,
                )
            )
            db.session.commit()

        EnterprisePlatformService.ensure_defaults()
        ApiClientService.ensure_defaults()

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
        checks["security_dashboard"] = {"ok": web_ok, "routes": web_results}

        api_ok = True
        api_results = {}
        for route in API_ROUTES:
            response = client.get(route, follow_redirects=True)
            ok = response.status_code == 200
            api_ok = api_ok and ok
            api_results[route] = {"status_code": response.status_code, "ok": ok}
        checks["api_endpoints"] = {"ok": api_ok, "routes": api_results}

        from app.services.security_compliance_service import FEATURES, dashboard_payload, security_readiness_report

        dashboard = dashboard_payload()
        readiness = security_readiness_report()
        checks["feature_coverage"] = {
            "ok": len(dashboard.get("features", [])) == 12 and list(FEATURES) == dashboard.get("features"),
            "features": len(FEATURES),
        }

        checks["secret_management_audit"] = {
            "ok": _api_json(client.get("/api/v1/security-compliance/secrets")).get("read_only") is True,
        }
        checks["api_key_rotation"] = {
            "ok": "keys" in _api_json(client.get("/api/v1/security-compliance/api-keys")),
        }
        checks["jwt_audit"] = {
            "ok": _api_json(client.get("/api/v1/security-compliance/jwt")).get("read_only") is True,
        }
        checks["rbac_permission_matrix"] = {
            "ok": "platform_roles" in _api_json(client.get("/api/v1/security-compliance/rbac")),
        }
        checks["audit_log_viewer"] = {
            "ok": _api_json(client.get("/api/v1/security-compliance/audit")).get("read_only") is True,
        }
        checks["security_event_timeline"] = {
            "ok": "timeline" in _api_json(client.get("/api/v1/security-compliance/timeline")),
        }
        checks["failed_login_analytics"] = {
            "ok": _api_json(client.get("/api/v1/security-compliance/failed-logins")).get("read_only") is True,
        }
        checks["ip_whitelist_framework"] = {
            "ok": "rules" in _api_json(client.get("/api/v1/security-compliance/ip-whitelist")),
        }
        checks["rate_limit_dashboard"] = {
            "ok": _api_json(client.get("/api/v1/security-compliance/rate-limits")).get("enabled") is not None,
        }
        checks["phi_access_audit"] = {
            "ok": _api_json(client.get("/api/v1/security-compliance/phi-access")).get("read_only") is True,
        }
        checks["compliance_report"] = {
            "ok": _api_json(client.get("/api/v1/security-compliance/compliance")).get("pilot_ready") is not None,
        }

        keys = _api_json(client.get("/api/v1/security-compliance/api-keys"))
        active_key = next((item for item in keys.get("keys", []) if item.get("status") == "ACTIVE"), None)
        if active_key:
            rotated = _api_json(
                client.post(f"/api/v1/security-compliance/api-keys/{active_key['id']}/rotate")
            )
            checks["api_key_rotation_action"] = {"ok": rotated.get("rotated") is True}
        else:
            checks["api_key_rotation_action"] = {"ok": True, "skipped": "no active key"}

        legacy = client.get("/audit")
        checks["legacy_audit_center_preserved"] = {"ok": legacy.status_code == 200}

        existing = client.get("/api/v1/admin-security/health")
        checks["existing_admin_security_preserved"] = {
            "ok": existing.status_code in (200, 401),
        }

    passed = sum(1 for item in checks.values() if item.get("ok"))
    total = len(checks)
    score = round((passed / total) * 100, 1) if total else 0.0
    report = {
        "generated_at": utc_now(),
        "phase": "5.1",
        "sprint": "Security & Compliance",
        "summary": {
            "score": score,
            "checks_passed": passed,
            "checks_total": total,
            "ok": passed == total,
            "runtime_seconds": round(time.perf_counter() - start, 3),
        },
        "checks": checks,
        "readiness": readiness if "readiness" in locals() else {},
    }
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")

    print(f"Security & Compliance score: {score}%")
    print(f"Checks passed: {passed}/{total}")
    print(f"Report: {REPORT_PATH}")
    if report["summary"]["ok"]:
        print("SECURITY & COMPLIANCE VERIFY PASS\n")
        return 0
    print("SECURITY & COMPLIANCE VERIFY FAIL\n")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
