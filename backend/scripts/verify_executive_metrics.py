#!/usr/bin/env python3
"""Verify Executive Metrics Phase 5 Sprint 5.9."""

from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = ROOT / "generated_release" / "EXECUTIVE_METRICS_REPORT.json"

WEB_ROUTES = (
    "/executive-metrics",
    "/executive-metrics/revenue",
    "/executive-metrics/tat",
    "/executive-metrics/orders",
    "/executive-metrics/growth",
    "/executive-metrics/lab-sla",
    "/executive-metrics/collector-sla",
    "/executive-metrics/clinic-ranking",
    "/executive-metrics/doctor-ranking",
    "/executive-metrics/revenue-forecast",
)

API_ROUTES = (
    "/api/v1/executive-metrics/dashboard",
    "/api/v1/executive-metrics/revenue",
    "/api/v1/executive-metrics/tat",
    "/api/v1/executive-metrics/orders",
    "/api/v1/executive-metrics/growth",
    "/api/v1/executive-metrics/lab-sla",
    "/api/v1/executive-metrics/collector-sla",
    "/api/v1/executive-metrics/clinic-ranking",
    "/api/v1/executive-metrics/doctor-ranking",
    "/api/v1/executive-metrics/revenue-forecast",
    "/api/v1/executive-metrics/readiness",
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

    print("\n=== DXCON EXECUTIVE METRICS VERIFY ===\n")
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
                    email="verify-exec-metrics@demo.dxcon.test",
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
        checks["executive_metrics_dashboard"] = {"ok": web_ok, "routes": web_results}

        api_ok = True
        api_results = {}
        for route in API_ROUTES:
            response = client.get(route, follow_redirects=True)
            ok = response.status_code == 200
            api_ok = api_ok and ok
            api_results[route] = {"status_code": response.status_code, "ok": ok}
        checks["api_endpoints"] = {"ok": api_ok, "routes": api_results}

        from app.services.executive_metrics_service import FEATURES

        dashboard = _api_json(client.get("/api/v1/executive-metrics/dashboard"))
        checks["feature_coverage"] = {
            "ok": len(dashboard.get("features", [])) == 9 and list(FEATURES) == dashboard.get("features"),
            "features": len(FEATURES),
        }

        checks["revenue"] = {
            "ok": _api_json(client.get("/api/v1/executive-metrics/revenue")).get("report") == "revenue_metrics",
        }
        checks["tat"] = {
            "ok": _api_json(client.get("/api/v1/executive-metrics/tat")).get("report") == "tat_metrics",
        }
        checks["orders"] = {
            "ok": _api_json(client.get("/api/v1/executive-metrics/orders")).get("report") == "orders_metrics",
        }
        checks["growth"] = {
            "ok": "growth" in _api_json(client.get("/api/v1/executive-metrics/growth")),
        }
        checks["lab_sla"] = {
            "ok": _api_json(client.get("/api/v1/executive-metrics/lab-sla")).get("report") == "lab_sla_metrics",
        }
        checks["collector_sla"] = {
            "ok": _api_json(client.get("/api/v1/executive-metrics/collector-sla")).get("report")
            == "collector_sla_metrics",
        }
        checks["clinic_ranking"] = {
            "ok": "rankings" in _api_json(client.get("/api/v1/executive-metrics/clinic-ranking")),
        }
        checks["doctor_ranking"] = {
            "ok": "rankings" in _api_json(client.get("/api/v1/executive-metrics/doctor-ranking")),
        }
        checks["revenue_forecast"] = {
            "ok": "forecast" in _api_json(client.get("/api/v1/executive-metrics/revenue-forecast")),
        }

        legacy_analytics = client.get("/enterprise-analytics", follow_redirects=True)
        checks["legacy_enterprise_analytics_preserved"] = {"ok": legacy_analytics.status_code == 200}

        legacy_executive = client.get("/executive-v9", follow_redirects=True)
        checks["legacy_executive_v9_preserved"] = {"ok": legacy_executive.status_code == 200}

        legacy_api = client.get("/api/v1/enterprise-analytics/dashboard", follow_redirects=True)
        checks["legacy_enterprise_analytics_api_preserved"] = {"ok": legacy_api.status_code == 200}

        legacy_dashboard = _api_json(client.get("/api/v1/dashboard/summary"))
        checks["legacy_dashboard_summary_preserved"] = {
            "ok": isinstance(legacy_dashboard, dict) and len(legacy_dashboard) > 0,
        }

    passed = sum(1 for item in checks.values() if item.get("ok"))
    total = len(checks)
    score = round((passed / total) * 100, 1) if total else 0.0
    report = {
        "generated_at": utc_now(),
        "phase": "5.9",
        "sprint": "Executive Metrics",
        "summary": {
            "score": score,
            "checks_passed": passed,
            "checks_total": total,
            "ok": passed == total,
            "runtime_seconds": round(time.perf_counter() - start, 3),
        },
        "checks": checks,
        "readiness": _api_json(client.get("/api/v1/executive-metrics/readiness")) if "client" in locals() else {},
    }
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")

    print(f"Executive Metrics score: {score}%")
    print(f"Checks passed: {passed}/{total}")
    print(f"Report: {REPORT_PATH}")
    if report["summary"]["ok"]:
        print("EXECUTIVE METRICS VERIFY PASS\n")
        return 0
    print("EXECUTIVE METRICS VERIFY FAIL\n")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
