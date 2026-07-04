#!/usr/bin/env python3
"""Verify Monitoring Center Phase 5 Sprint 5.2."""

from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = ROOT / "generated_release" / "MONITORING_CENTER_REPORT.json"

WEB_ROUTES = (
    "/monitoring",
    "/monitoring/application",
    "/monitoring/queues",
    "/monitoring/database",
    "/monitoring/redis",
    "/monitoring/latency",
    "/monitoring/errors",
    "/monitoring/jobs",
    "/monitoring/kpi",
    "/monitoring/alerts",
)

API_ROUTES = (
    "/api/v1/monitoring-center/dashboard",
    "/api/v1/monitoring-center/application",
    "/api/v1/monitoring-center/queues",
    "/api/v1/monitoring-center/database",
    "/api/v1/monitoring-center/redis",
    "/api/v1/monitoring-center/latency",
    "/api/v1/monitoring-center/errors",
    "/api/v1/monitoring-center/jobs",
    "/api/v1/monitoring-center/kpi",
    "/api/v1/monitoring-center/alerts",
    "/api/v1/monitoring-center/readiness",
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

    print("\n=== DXCON MONITORING CENTER VERIFY ===\n")
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
                    email="verify-monitoring@demo.dxcon.test",
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
        checks["monitoring_dashboard"] = {"ok": web_ok, "routes": web_results}

        api_ok = True
        api_results = {}
        for route in API_ROUTES:
            response = client.get(route, follow_redirects=True)
            ok = response.status_code == 200
            api_ok = api_ok and ok
            api_results[route] = {"status_code": response.status_code, "ok": ok}
        checks["api_endpoints"] = {"ok": api_ok, "routes": api_results}

        from app.services.monitoring_center_service import FEATURES, dashboard_payload, monitoring_readiness_report

        dashboard = dashboard_payload()
        readiness = monitoring_readiness_report()
        checks["feature_coverage"] = {
            "ok": len(dashboard.get("features", [])) == 9 and list(FEATURES) == dashboard.get("features"),
            "features": len(FEATURES),
        }

        checks["application_health"] = {
            "ok": _api_json(client.get("/api/v1/monitoring-center/application")).get("read_only") is True,
        }
        checks["queue_health"] = {
            "ok": "summary" in _api_json(client.get("/api/v1/monitoring-center/queues")),
        }
        checks["database_health"] = {
            "ok": _api_json(client.get("/api/v1/monitoring-center/database")).get("read_only") is True,
        }
        checks["redis_health"] = {
            "ok": "ping" in _api_json(client.get("/api/v1/monitoring-center/redis")),
        }
        checks["api_latency"] = {
            "ok": "average_ms" in _api_json(client.get("/api/v1/monitoring-center/latency")),
        }
        checks["error_rate"] = {
            "ok": "error_rate_percent" in _api_json(client.get("/api/v1/monitoring-center/errors")),
        }
        checks["background_jobs"] = {
            "ok": "runner" in _api_json(client.get("/api/v1/monitoring-center/jobs")),
        }
        checks["business_kpi"] = {
            "ok": "observability" in _api_json(client.get("/api/v1/monitoring-center/kpi")),
        }
        checks["alerts"] = {
            "ok": "rules" in _api_json(client.get("/api/v1/monitoring-center/alerts")),
        }

        legacy = client.get("/monitor")
        checks["legacy_monitor_preserved"] = {"ok": legacy.status_code == 200}

        system_health = client.get("/api/v1/system/health")
        checks["existing_system_health_preserved"] = {"ok": system_health.status_code == 200}

    passed = sum(1 for item in checks.values() if item.get("ok"))
    total = len(checks)
    score = round((passed / total) * 100, 1) if total else 0.0
    report = {
        "generated_at": utc_now(),
        "phase": "5.2",
        "sprint": "Monitoring Center",
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

    print(f"Monitoring Center score: {score}%")
    print(f"Checks passed: {passed}/{total}")
    print(f"Report: {REPORT_PATH}")
    if report["summary"]["ok"]:
        print("MONITORING CENTER VERIFY PASS\n")
        return 0
    print("MONITORING CENTER VERIFY FAIL\n")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
