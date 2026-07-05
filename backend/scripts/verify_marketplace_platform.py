#!/usr/bin/env python3
"""Verify Marketplace Platform Phase 7.2."""

from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
REPORT_PATH = ROOT / "generated_release" / "MARKETPLACE_PLATFORM_REPORT.json"
SDK_DOC = REPO / "docs" / "PLUGIN_SDK_GUIDE.md"

WEB_ROUTES = (
    "/marketplace-platform",
    "/marketplace-platform/marketplace",
    "/marketplace-platform/registry",
    "/marketplace-platform/manifest",
    "/marketplace-platform/installer",
    "/marketplace-platform/versions",
    "/marketplace-platform/dependencies",
    "/marketplace-platform/permissions",
    "/marketplace-platform/sandbox",
    "/marketplace-platform/health",
)

API_ROUTES = (
    "/api/v1/marketplace-platform/dashboard",
    "/api/v1/marketplace-platform/marketplace",
    "/api/v1/marketplace-platform/registry",
    "/api/v1/marketplace-platform/manifest",
    "/api/v1/marketplace-platform/installer",
    "/api/v1/marketplace-platform/versions",
    "/api/v1/marketplace-platform/dependencies",
    "/api/v1/marketplace-platform/permissions",
    "/api/v1/marketplace-platform/sandbox",
    "/api/v1/marketplace-platform/health",
    "/api/v1/marketplace-platform/readiness",
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

    print("\n=== DXCON MARKETPLACE PLATFORM VERIFY ===\n")
    start = time.perf_counter()
    checks: dict[str, dict] = {}

    from app import create_app

    app = create_app()
    with app.app_context():
        from app.core.passwords import hash_password
        from app.extensions.db import db
        from app.models.user import User
        from app.services.marketplace_platform_service import FEATURES, ensure_marketplace_platform

        db.create_all()
        if not User.query.filter(User.role.in_(("SUPER_ADMIN", "ADMIN"))).first():
            db.session.add(
                User(
                    email="verify-marketplace-platform@demo.dxcon.test",
                    role="ADMIN",
                    password_hash=hash_password("DemoPass123!"),
                    is_active=True,
                )
            )
            db.session.commit()

        ensure_marketplace_platform()

        routes = {str(rule.rule) for rule in app.url_map.iter_rules()}
        missing_web = [route for route in WEB_ROUTES if route not in routes]
        missing_api = [route for route in API_ROUTES if route not in routes]
        checks["route_registry"] = {
            "ok": not missing_web and not missing_api,
            "missing_web": missing_web,
            "missing_api": missing_api,
        }

        checks["sdk_guide"] = {"ok": SDK_DOC.exists(), "path": str(SDK_DOC.relative_to(REPO))}

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

        dashboard = _api_json(client.get("/api/v1/marketplace-platform/dashboard"))
        checks["feature_coverage"] = {
            "ok": len(dashboard.get("features", [])) == 9 and list(FEATURES) == dashboard.get("features"),
            "features": len(FEATURES),
        }

        checks["marketplace"] = {
            "ok": _api_json(client.get("/api/v1/marketplace-platform/marketplace")).get("report") == "marketplace_overview",
        }
        checks["plugin_registry"] = {
            "ok": _api_json(client.get("/api/v1/marketplace-platform/registry")).get("report") == "plugin_registry",
        }
        checks["plugin_manifest"] = {
            "ok": _api_json(client.get("/api/v1/marketplace-platform/manifest")).get("report") == "plugin_manifest",
        }
        checks["plugin_installer"] = {
            "ok": "installs" in _api_json(client.get("/api/v1/marketplace-platform/installer")),
        }
        checks["plugin_version"] = {
            "ok": _api_json(client.get("/api/v1/marketplace-platform/versions")).get("report") == "plugin_version",
        }
        checks["plugin_dependency"] = {
            "ok": _api_json(client.get("/api/v1/marketplace-platform/dependencies")).get("report") == "plugin_dependency",
        }
        checks["plugin_permission"] = {
            "ok": _api_json(client.get("/api/v1/marketplace-platform/permissions")).get("report") == "plugin_permission",
        }
        checks["plugin_sandbox"] = {
            "ok": "results" in _api_json(client.get("/api/v1/marketplace-platform/sandbox")),
        }
        checks["plugin_health"] = {
            "ok": _api_json(client.get("/api/v1/marketplace-platform/health")).get("report") == "plugin_health",
        }

        legacy_marketplace = client.get("/marketplace", follow_redirects=True)
        checks["legacy_marketplace_preserved"] = {"ok": legacy_marketplace.status_code == 200}

        legacy_plugins = client.get("/api/v1/plugins", follow_redirects=True)
        checks["legacy_plugins_api_preserved"] = {"ok": legacy_plugins.status_code == 200}

    passed = sum(1 for item in checks.values() if item.get("ok"))
    total = len(checks)
    score = round((passed / total) * 100, 1) if total else 0.0
    report = {
        "generated_at": utc_now(),
        "phase": "7.2",
        "sprint": "Marketplace",
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

    print(f"Marketplace Platform score: {score}%")
    print(f"Checks passed: {passed}/{total}")
    print(f"Report: {REPORT_PATH}")
    if report["summary"]["ok"]:
        print("MARKETPLACE PLATFORM VERIFY PASS\n")
        return 0
    print("MARKETPLACE PLATFORM VERIFY FAIL\n")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
