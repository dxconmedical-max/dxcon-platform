#!/usr/bin/env python3
"""Verify Release Management Phase 5 Sprint 5.7."""

from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = ROOT / "generated_release" / "RELEASE_MANAGEMENT_REPORT.json"

WEB_ROUTES = (
    "/release-management",
    "/release-management/environment",
    "/release-management/version",
    "/release-management/notes",
    "/release-management/migration",
    "/release-management/health",
    "/release-management/rollback",
)

API_ROUTES = (
    "/api/v1/release-management/dashboard",
    "/api/v1/release-management/environment",
    "/api/v1/release-management/version",
    "/api/v1/release-management/notes",
    "/api/v1/release-management/migration",
    "/api/v1/release-management/health",
    "/api/v1/release-management/rollback",
    "/api/v1/release-management/inventory",
    "/api/v1/release-management/readiness",
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

    print("\n=== DXCON RELEASE MANAGEMENT VERIFY ===\n")
    start = time.perf_counter()
    checks: dict[str, dict] = {}

    from app import create_app

    app = create_app()
    with app.app_context():
        from app.core.passwords import hash_password
        from app.extensions.db import db
        from app.models.user import User
        from app.operations.deployment_service import DeploymentService

        db.create_all()
        if not User.query.filter(User.role.in_(("SUPER_ADMIN", "ADMIN"))).first():
            db.session.add(
                User(
                    email="verify-release@demo.dxcon.test",
                    role="ADMIN",
                    password_hash=hash_password("DemoPass123!"),
                    is_active=True,
                )
            )
            db.session.commit()

        DeploymentService.run_checklist()

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
        checks["release_dashboard"] = {"ok": web_ok, "routes": web_results}

        api_ok = True
        api_results = {}
        for route in API_ROUTES:
            response = client.get(route, follow_redirects=True)
            ok = response.status_code == 200
            api_ok = api_ok and ok
            api_results[route] = {"status_code": response.status_code, "ok": ok}
        checks["api_endpoints"] = {"ok": api_ok, "routes": api_results}

        from app.services.release_management_service import FEATURES

        dashboard = _api_json(client.get("/api/v1/release-management/dashboard"))
        checks["feature_coverage"] = {
            "ok": len(dashboard.get("features", [])) == 6 and list(FEATURES) == dashboard.get("features"),
            "features": len(FEATURES),
        }

        checks["environment"] = {
            "ok": "app_env" in _api_json(client.get("/api/v1/release-management/environment")),
        }
        checks["version"] = {
            "ok": bool(_api_json(client.get("/api/v1/release-management/version")).get("version")),
        }
        checks["release_notes"] = {
            "ok": len(_api_json(client.get("/api/v1/release-management/notes")).get("notes", [])) >= 1,
        }
        checks["migration_status"] = {
            "ok": _api_json(client.get("/api/v1/release-management/migration")).get("status") == "READY",
        }
        checks["health"] = {
            "ok": _api_json(client.get("/api/v1/release-management/health")).get("live", {}).get("status_code") in {200, 503},
        }
        checks["rollback"] = {
            "ok": len(_api_json(client.get("/api/v1/release-management/rollback")).get("items", [])) >= 4,
        }

        legacy_deploy = _api_json(client.get("/api/v1/operations/deployment"))
        checks["legacy_operations_deployment_preserved"] = {
            "ok": legacy_deploy.get("current_version") is not None,
        }

        legacy_health = client.get("/api/v1/system/health")
        checks["legacy_system_health_preserved"] = {"ok": legacy_health.status_code in {200, 503}}

        prod_hub = client.get("/production-deployment")
        checks["legacy_production_deployment_preserved"] = {"ok": prod_hub.status_code == 200}

    passed = sum(1 for item in checks.values() if item.get("ok"))
    total = len(checks)
    score = round((passed / total) * 100, 1) if total else 0.0
    report = {
        "generated_at": utc_now(),
        "phase": "5.7",
        "sprint": "Release Management",
        "summary": {
            "score": score,
            "checks_passed": passed,
            "checks_total": total,
            "ok": passed == total,
            "runtime_seconds": round(time.perf_counter() - start, 3),
        },
        "checks": checks,
        "readiness": _api_json(client.get("/api/v1/release-management/readiness")) if "client" in locals() else {},
    }
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")

    print(f"Release Management score: {score}%")
    print(f"Checks passed: {passed}/{total}")
    print(f"Report: {REPORT_PATH}")
    if report["summary"]["ok"]:
        print("RELEASE MANAGEMENT VERIFY PASS\n")
        return 0
    print("RELEASE MANAGEMENT VERIFY FAIL\n")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
