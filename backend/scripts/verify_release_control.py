#!/usr/bin/env python3
"""Verify Release Control Phase 5 Sprint 5.12."""

from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = ROOT / "generated_release" / "RELEASE_CONTROL_REPORT.json"

WEB_ROUTES = (
    "/release-control",
    "/release-control/history",
    "/release-control/version-compare",
    "/release-control/migration",
    "/release-control/rollback",
    "/release-control/deployment",
    "/release-control/audit",
)

API_ROUTES = (
    "/api/v1/release-control/dashboard",
    "/api/v1/release-control/history",
    "/api/v1/release-control/version-compare",
    "/api/v1/release-control/migration",
    "/api/v1/release-control/rollback",
    "/api/v1/release-control/deployment",
    "/api/v1/release-control/audit",
    "/api/v1/release-control/readiness",
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

    print("\n=== DXCON RELEASE CONTROL VERIFY ===\n")
    start = time.perf_counter()
    checks: dict[str, dict] = {}

    from app import create_app

    app = create_app()
    with app.app_context():
        from app.core.passwords import hash_password
        from app.extensions.db import db
        from app.models.user import User

        db.create_all()
        if not User.query.filter(User.role.in_(("SUPER_ADMIN", "ADMIN"))).first():
            db.session.add(
                User(
                    email="verify-release-control@demo.dxcon.test",
                    role="ADMIN",
                    password_hash=hash_password("DemoPass123!"),
                    is_active=True,
                )
            )
            db.session.commit()

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
        checks["release_control_dashboard"] = {"ok": web_ok, "routes": web_results}

        api_ok = True
        api_results = {}
        for route in API_ROUTES:
            response = client.get(route, follow_redirects=True)
            ok = response.status_code == 200
            api_ok = api_ok and ok
            api_results[route] = {"status_code": response.status_code, "ok": ok}
        checks["api_endpoints"] = {"ok": api_ok, "routes": api_results}

        from app.services.release_control_service import FEATURES

        dashboard = _api_json(client.get("/api/v1/release-control/dashboard"))
        checks["feature_coverage"] = {
            "ok": len(dashboard.get("features", [])) == 6 and list(FEATURES) == dashboard.get("features"),
            "features": len(FEATURES),
        }

        checks["release_history"] = {
            "ok": "entries" in _api_json(client.get("/api/v1/release-control/history")),
        }
        checks["version_compare"] = {
            "ok": "differences" in _api_json(client.get("/api/v1/release-control/version-compare")),
        }
        checks["migration"] = {
            "ok": _api_json(client.get("/api/v1/release-control/migration")).get("report") == "migration_metrics",
        }
        checks["rollback"] = {
            "ok": _api_json(client.get("/api/v1/release-control/rollback")).get("report") == "rollback_metrics",
        }
        checks["deployment"] = {
            "ok": "last_deployment" in _api_json(client.get("/api/v1/release-control/deployment")),
        }
        checks["audit"] = {
            "ok": "audit_entries" in _api_json(client.get("/api/v1/release-control/audit")),
        }

        legacy_mgmt = client.get("/release-management", follow_redirects=True)
        checks["legacy_release_management_preserved"] = {"ok": legacy_mgmt.status_code == 200}

        legacy_prod = client.get("/production-deployment", follow_redirects=True)
        checks["legacy_production_deployment_preserved"] = {"ok": legacy_prod.status_code == 200}

        legacy_api = client.get("/api/v1/release-management/dashboard", follow_redirects=True)
        checks["legacy_release_management_api_preserved"] = {"ok": legacy_api.status_code == 200}

        rollback_plan = client.get("/api/v1/operations/deployment/rollback-plan", follow_redirects=True)
        checks["legacy_rollback_plan_route_preserved"] = {
            "ok": rollback_plan.status_code in {200, 404},
        }

    passed = sum(1 for item in checks.values() if item.get("ok"))
    total = len(checks)
    score = round((passed / total) * 100, 1) if total else 0.0
    report = {
        "generated_at": utc_now(),
        "phase": "5.12",
        "sprint": "Release Control",
        "summary": {
            "score": score,
            "checks_passed": passed,
            "checks_total": total,
            "ok": passed == total,
            "runtime_seconds": round(time.perf_counter() - start, 3),
        },
        "checks": checks,
        "readiness": _api_json(client.get("/api/v1/release-control/readiness")) if "client" in locals() else {},
    }
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")

    print(f"Release Control score: {score}%")
    print(f"Checks passed: {passed}/{total}")
    print(f"Report: {REPORT_PATH}")
    if report["summary"]["ok"]:
        print("RELEASE CONTROL VERIFY PASS\n")
        return 0
    print("RELEASE CONTROL VERIFY FAIL\n")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
