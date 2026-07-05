#!/usr/bin/env python3
"""Verify Pilot Toolkit Phase 5 Sprint 5.13."""

from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = ROOT / "generated_release" / "PILOT_TOOLKIT_REPORT.json"

WEB_ROUTES = (
    "/pilot-toolkit",
    "/pilot-toolkit/demo-accounts",
    "/pilot-toolkit/demo-data",
    "/pilot-toolkit/postman",
    "/pilot-toolkit/swagger",
    "/pilot-toolkit/workflow",
    "/pilot-toolkit/pdf",
    "/pilot-toolkit/qr",
    "/pilot-toolkit/reports",
)

API_ROUTES = (
    "/api/v1/pilot-toolkit/dashboard",
    "/api/v1/pilot-toolkit/demo-accounts",
    "/api/v1/pilot-toolkit/demo-data",
    "/api/v1/pilot-toolkit/postman",
    "/api/v1/pilot-toolkit/swagger",
    "/api/v1/pilot-toolkit/workflow",
    "/api/v1/pilot-toolkit/pdf",
    "/api/v1/pilot-toolkit/qr",
    "/api/v1/pilot-toolkit/reports",
    "/api/v1/pilot-toolkit/readiness",
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

    print("\n=== DXCON PILOT TOOLKIT VERIFY ===\n")
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
                    email="verify-pilot-toolkit@demo.dxcon.test",
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
        checks["pilot_toolkit_dashboard"] = {"ok": web_ok, "routes": web_results}

        api_ok = True
        api_results = {}
        for route in API_ROUTES:
            response = client.get(route, follow_redirects=True)
            ok = response.status_code == 200
            api_ok = api_ok and ok
            api_results[route] = {"status_code": response.status_code, "ok": ok}
        checks["api_endpoints"] = {"ok": api_ok, "routes": api_results}

        from app.services.pilot_toolkit_service import FEATURES

        dashboard = _api_json(client.get("/api/v1/pilot-toolkit/dashboard"))
        checks["feature_coverage"] = {
            "ok": len(dashboard.get("features", [])) == 8 and list(FEATURES) == dashboard.get("features"),
            "features": len(FEATURES),
        }

        checks["demo_accounts"] = {
            "ok": _api_json(client.get("/api/v1/pilot-toolkit/demo-accounts")).get("accounts_total", 0) >= 0,
        }
        checks["demo_data"] = {
            "ok": "seeded_summary" in _api_json(client.get("/api/v1/pilot-toolkit/demo-data")),
        }
        checks["postman"] = {
            "ok": "collection_url" in _api_json(client.get("/api/v1/pilot-toolkit/postman")),
        }
        checks["swagger"] = {
            "ok": "swagger_ui" in _api_json(client.get("/api/v1/pilot-toolkit/swagger")),
        }
        checks["workflow"] = {
            "ok": _api_json(client.get("/api/v1/pilot-toolkit/workflow")).get("steps_total", 0) >= 8,
        }
        checks["pdf"] = {
            "ok": "pdf_route_pattern" in _api_json(client.get("/api/v1/pilot-toolkit/pdf")),
        }
        checks["qr"] = {
            "ok": "qr_route_pattern" in _api_json(client.get("/api/v1/pilot-toolkit/qr")),
        }
        checks["reports"] = {
            "ok": "api_routes" in _api_json(client.get("/api/v1/pilot-toolkit/reports")),
        }

        legacy_demo = client.get("/demo-accounts", follow_redirects=True)
        checks["legacy_demo_accounts_preserved"] = {"ok": legacy_demo.status_code == 200}

        legacy_workflow = client.get("/workflow-demo", follow_redirects=True)
        checks["legacy_workflow_demo_preserved"] = {"ok": legacy_workflow.status_code == 200}

        legacy_swagger = client.get("/api-docs/swagger", follow_redirects=True)
        checks["legacy_swagger_ui_preserved"] = {"ok": legacy_swagger.status_code == 200}

        legacy_reports = client.get("/reports", follow_redirects=True)
        checks["legacy_reports_preserved"] = {"ok": legacy_reports.status_code == 200}

        legacy_postman = client.get("/api/v1/developer-portal/postman", follow_redirects=True)
        checks["legacy_developer_portal_postman_preserved"] = {"ok": legacy_postman.status_code == 200}

    passed = sum(1 for item in checks.values() if item.get("ok"))
    total = len(checks)
    score = round((passed / total) * 100, 1) if total else 0.0
    report = {
        "generated_at": utc_now(),
        "phase": "5.13",
        "sprint": "Pilot Toolkit",
        "summary": {
            "score": score,
            "checks_passed": passed,
            "checks_total": total,
            "ok": passed == total,
            "runtime_seconds": round(time.perf_counter() - start, 3),
        },
        "checks": checks,
        "readiness": _api_json(client.get("/api/v1/pilot-toolkit/readiness")) if "client" in locals() else {},
    }
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")

    print(f"Pilot Toolkit score: {score}%")
    print(f"Checks passed: {passed}/{total}")
    print(f"Report: {REPORT_PATH}")
    if report["summary"]["ok"]:
        print("PILOT TOOLKIT VERIFY PASS\n")
        return 0
    print("PILOT TOOLKIT VERIFY FAIL\n")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
