#!/usr/bin/env python3
"""Verify AI Operations Phase 5 Sprint 5.10."""

from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = ROOT / "generated_release" / "AI_OPERATIONS_REPORT.json"

WEB_ROUTES = (
    "/ai-operations",
    "/ai-operations/incident-summary",
    "/ai-operations/usage",
    "/ai-operations/cost",
    "/ai-operations/accuracy",
    "/ai-operations/model-health",
    "/ai-operations/prompt-version",
)

API_ROUTES = (
    "/api/v1/ai-operations/dashboard",
    "/api/v1/ai-operations/incident-summary",
    "/api/v1/ai-operations/usage",
    "/api/v1/ai-operations/cost",
    "/api/v1/ai-operations/accuracy",
    "/api/v1/ai-operations/model-health",
    "/api/v1/ai-operations/prompt-version",
    "/api/v1/ai-operations/readiness",
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

    print("\n=== DXCON AI OPERATIONS VERIFY ===\n")
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
                    email="verify-ai-ops@demo.dxcon.test",
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
        checks["ai_operations_dashboard"] = {"ok": web_ok, "routes": web_results}

        api_ok = True
        api_results = {}
        for route in API_ROUTES:
            response = client.get(route, follow_redirects=True)
            ok = response.status_code == 200
            api_ok = api_ok and ok
            api_results[route] = {"status_code": response.status_code, "ok": ok}
        checks["api_endpoints"] = {"ok": api_ok, "routes": api_results}

        from app.services.ai_operations_service import FEATURES

        dashboard = _api_json(client.get("/api/v1/ai-operations/dashboard"))
        checks["feature_coverage"] = {
            "ok": len(dashboard.get("features", [])) == 6 and list(FEATURES) == dashboard.get("features"),
            "features": len(FEATURES),
        }

        checks["incident_summary"] = {
            "ok": "summary" in _api_json(client.get("/api/v1/ai-operations/incident-summary")),
        }
        checks["usage"] = {
            "ok": "usage" in _api_json(client.get("/api/v1/ai-operations/usage")),
        }
        checks["cost"] = {
            "ok": "totals" in _api_json(client.get("/api/v1/ai-operations/cost")),
        }
        checks["accuracy"] = {
            "ok": "success_rate_percent" in _api_json(client.get("/api/v1/ai-operations/accuracy")),
        }
        checks["model_health"] = {
            "ok": "models" in _api_json(client.get("/api/v1/ai-operations/model-health")),
        }
        checks["prompt_version"] = {
            "ok": "prompts" in _api_json(client.get("/api/v1/ai-operations/prompt-version")),
        }

        legacy_usage = client.get("/api/v1/ai-platform/usage", follow_redirects=True)
        checks["legacy_ai_platform_usage_preserved"] = {"ok": legacy_usage.status_code == 200}

        legacy_prompts = client.get("/api/v1/ai-platform/prompts", follow_redirects=True)
        checks["legacy_ai_platform_prompts_preserved"] = {"ok": legacy_prompts.status_code == 200}

        legacy_analytics = client.get("/enterprise-analytics/ai", follow_redirects=True)
        checks["legacy_enterprise_analytics_ai_preserved"] = {"ok": legacy_analytics.status_code == 200}

    passed = sum(1 for item in checks.values() if item.get("ok"))
    total = len(checks)
    score = round((passed / total) * 100, 1) if total else 0.0
    report = {
        "generated_at": utc_now(),
        "phase": "5.10",
        "sprint": "AI Operations",
        "summary": {
            "score": score,
            "checks_passed": passed,
            "checks_total": total,
            "ok": passed == total,
            "runtime_seconds": round(time.perf_counter() - start, 3),
        },
        "checks": checks,
        "readiness": _api_json(client.get("/api/v1/ai-operations/readiness")) if "client" in locals() else {},
    }
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")

    print(f"AI Operations score: {score}%")
    print(f"Checks passed: {passed}/{total}")
    print(f"Report: {REPORT_PATH}")
    if report["summary"]["ok"]:
        print("AI OPERATIONS VERIFY PASS\n")
        return 0
    print("AI OPERATIONS VERIFY FAIL\n")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
