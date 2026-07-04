#!/usr/bin/env python3
"""Verify Production Deployment Phase 5 Sprint 5.5."""

from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = ROOT / "generated_release" / "PRODUCTION_DEPLOYMENT_REPORT.json"

WEB_ROUTES = (
    "/production-deployment",
    "/production-deployment/docker",
    "/production-deployment/nginx",
    "/production-deployment/probes",
    "/production-deployment/rolling",
    "/production-deployment/migration",
    "/production-deployment/release",
    "/production-deployment/rollback",
)

API_ROUTES = (
    "/api/v1/production-deployment/dashboard",
    "/api/v1/production-deployment/docker",
    "/api/v1/production-deployment/nginx",
    "/api/v1/production-deployment/probes",
    "/api/v1/production-deployment/rolling",
    "/api/v1/production-deployment/migration",
    "/api/v1/production-deployment/release",
    "/api/v1/production-deployment/rollback",
    "/api/v1/production-deployment/inventory",
    "/api/v1/production-deployment/readiness",
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

    print("\n=== DXCON PRODUCTION DEPLOYMENT VERIFY ===\n")
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
                    email="verify-deploy@demo.dxcon.test",
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
        checks["production_dashboard"] = {"ok": web_ok, "routes": web_results}

        api_ok = True
        api_results = {}
        for route in API_ROUTES:
            response = client.get(route, follow_redirects=True)
            ok = response.status_code == 200
            api_ok = api_ok and ok
            api_results[route] = {"status_code": response.status_code, "ok": ok}
        checks["api_endpoints"] = {"ok": api_ok, "routes": api_results}

        from app.services.production_deployment_service import FEATURES

        dashboard = _api_json(client.get("/api/v1/production-deployment/dashboard"))
        checks["feature_coverage"] = {
            "ok": len(dashboard.get("features", [])) == 7 and list(FEATURES) == dashboard.get("features"),
            "features": len(FEATURES),
        }

        docker = _api_json(client.get("/api/v1/production-deployment/docker"))
        checks["docker_production_profile"] = {
            "ok": docker.get("checks_passed", 0) >= 7,
        }
        nginx = _api_json(client.get("/api/v1/production-deployment/nginx"))
        checks["nginx_production"] = {
            "ok": nginx.get("checks_passed", 0) >= 8,
        }
        probes = _api_json(client.get("/api/v1/production-deployment/probes"))
        checks["health_probes"] = {
            "ok": probes.get("live_probe", {}).get("status_code") in {200, 503},
        }
        rolling = _api_json(client.get("/api/v1/production-deployment/rolling"))
        checks["rolling_deployment"] = {
            "ok": rolling.get("replicas", 0) >= 2 and rolling.get("pipeline_available"),
        }
        migration = _api_json(client.get("/api/v1/production-deployment/migration"))
        checks["zero_downtime_migration"] = {
            "ok": migration.get("checks_passed", 0) >= 4,
        }
        release = _api_json(client.get("/api/v1/production-deployment/release"))
        checks["release_checklist"] = {
            "ok": release.get("items_total", 0) >= 5,
        }
        rollback = _api_json(client.get("/api/v1/production-deployment/rollback"))
        checks["rollback_checklist"] = {
            "ok": len(rollback.get("items", [])) >= 5 and rollback.get("pipeline_available"),
        }

        legacy_deploy = _api_json(client.get("/api/v1/operations/deployment"))
        checks["legacy_operations_deployment_preserved"] = {
            "ok": legacy_deploy.get("current_version") is not None,
        }

        legacy_infra = client.get("/deployment")
        checks["legacy_deployment_web_preserved"] = {"ok": legacy_infra.status_code == 200}

    passed = sum(1 for item in checks.values() if item.get("ok"))
    total = len(checks)
    score = round((passed / total) * 100, 1) if total else 0.0
    report = {
        "generated_at": utc_now(),
        "phase": "5.5",
        "sprint": "Production Deployment",
        "summary": {
            "score": score,
            "checks_passed": passed,
            "checks_total": total,
            "ok": passed == total,
            "runtime_seconds": round(time.perf_counter() - start, 3),
        },
        "checks": checks,
        "readiness": _api_json(client.get("/api/v1/production-deployment/readiness")) if "client" in locals() else {},
    }
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")

    print(f"Production Deployment score: {score}%")
    print(f"Checks passed: {passed}/{total}")
    print(f"Report: {REPORT_PATH}")
    if report["summary"]["ok"]:
        print("PRODUCTION DEPLOYMENT VERIFY PASS\n")
        return 0
    print("PRODUCTION DEPLOYMENT VERIFY FAIL\n")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
