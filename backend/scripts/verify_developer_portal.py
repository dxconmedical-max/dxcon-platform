#!/usr/bin/env python3
"""Verify Partner Developer Portal Phase 4 Sprint 4.5."""

from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = ROOT / "generated_release" / "DEVELOPER_PORTAL_REPORT.json"

WEB_ROUTES = (
    "/developer",
    "/developer/api",
    "/developer/webhooks",
    "/developer/sandbox",
    "/developer/onboarding",
)

API_ROUTES = (
    "/api/v1/developer-portal/dashboard",
    "/api/v1/developer-portal/status",
    "/api/v1/developer-portal/docs",
    "/api/v1/developer-portal/sandbox/examples",
    "/api/v1/developer-portal/onboarding",
    "/api/v1/developer-portal/postman",
    "/api/v1/developer-portal/sdk",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


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

    print("\n=== DXCON PARTNER DEVELOPER PORTAL VERIFY ===\n")
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
                    email="verify-developer@demo.dxcon.test",
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

        web_ok = True
        web_results = {}
        for route in WEB_ROUTES:
            response = client.get(route, follow_redirects=True)
            ok = response.status_code == 200 and len(response.get_data(as_text=True)) > 200
            web_ok = web_ok and ok
            web_results[route] = {"status_code": response.status_code, "ok": ok}
        checks["developer_portal_landing"] = {"ok": web_ok, "routes": web_results}

        api_ok = True
        api_results = {}
        for route in API_ROUTES:
            response = client.get(route, follow_redirects=True)
            ok = response.status_code == 200
            api_ok = api_ok and ok
            api_results[route] = {"status_code": response.status_code, "ok": ok}
        checks["api_endpoints"] = {"ok": api_ok, "routes": api_results}

        from app.services.developer_portal_service import FEATURES, dashboard_payload

        dashboard = dashboard_payload(app)
        checks["feature_coverage"] = {
            "ok": len(dashboard.get("features", [])) == 10 and list(FEATURES) == dashboard.get("features"),
            "features": len(FEATURES),
        }

        docs = _api_json(client.get("/api/v1/developer-portal/docs"))
        checks["api_documentation_links"] = {
            "ok": bool(docs.get("documentation", {}).get("openapi_json")),
        }

        keys = docs.get("api_keys") or {}
        checks["api_key_instructions"] = {
            "ok": keys.get("header") == "X-API-Key" and len(keys.get("steps", [])) >= 4,
        }

        examples = _api_json(client.get("/api/v1/developer-portal/sandbox/examples"))
        checks["sandbox_payload_examples"] = {
            "ok": examples.get("sandbox") is True and "api_request" in examples and "adapters" in examples,
        }

        status = _api_json(client.get("/api/v1/developer-portal/status"))
        checks["integration_status_page"] = {
            "ok": "platform" in status and "integration_hub" in status,
        }

        sdk = _api_json(client.get("/api/v1/developer-portal/sdk"))
        checks["sdk_download_links"] = {
            "ok": sdk.get("available") is True and len(sdk.get("downloads", [])) >= 1,
        }

        python_sdk = client.get("/api/v1/developer-portal/sdk/python")
        checks["sdk_python_download"] = {
            "ok": python_sdk.status_code == 200 and "dxcon" in python_sdk.get_data(as_text=True).lower(),
        }

        postman = _api_json(client.get("/api/v1/developer-portal/postman"))
        checks["postman_collection_link"] = {
            "ok": postman.get("info", {}).get("name") == "DxCon Partner API",
        }

        onboarding = _api_json(client.get("/api/v1/developer-portal/onboarding"))
        checks["partner_onboarding_checklist"] = {
            "ok": len(onboarding.get("steps", [])) >= 6,
        }

        sandbox_run = _api_json(
            client.post(
                "/api/v1/developer-portal/sandbox/request",
                json={"method": "GET", "path": "/api/v1/api-platform/health"},
            )
        )
        checks["developer_sandbox_console"] = {
            "ok": sandbox_run.get("status_code") == 200,
        }

        webhook = _api_json(client.post("/api/v1/developer-portal/webhooks/test", json={}))
        checks["webhook_test_console"] = {
            "ok": "delivery" in webhook or "webhook" in webhook,
        }

        legacy = client.get("/developer/api-keys")
        checks["legacy_developer_routes_preserved"] = {
            "ok": legacy.status_code == 200,
        }

        existing = client.get("/api/v1/developer/sandbox/request", method="OPTIONS")
        checks["existing_sandbox_api_preserved"] = {
            "ok": existing.status_code in (200, 204, 405),
        }

    passed = sum(1 for item in checks.values() if item.get("ok"))
    total = len(checks)
    score = round((passed / total) * 100, 1) if total else 0.0
    report = {
        "generated_at": utc_now(),
        "phase": "4.5",
        "sprint": "Partner Developer Portal",
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

    print(f"Partner Developer Portal score: {score}%")
    print(f"Checks passed: {passed}/{total}")
    print(f"Report: {REPORT_PATH}")
    if report["summary"]["ok"]:
        print("PARTNER DEVELOPER PORTAL VERIFY PASS\n")
        return 0
    print("PARTNER DEVELOPER PORTAL VERIFY FAIL\n")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
