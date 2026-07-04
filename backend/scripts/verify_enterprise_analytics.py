#!/usr/bin/env python3
"""Verify Enterprise Analytics Expansion Phase 4 Sprint 4.6."""

from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = ROOT / "generated_release" / "ENTERPRISE_ANALYTICS_REPORT.json"

WEB_ROUTES = (
    "/enterprise-analytics",
    "/enterprise-analytics/revenue",
    "/enterprise-analytics/lab-sla",
    "/enterprise-analytics/collectors",
    "/enterprise-analytics/partners",
    "/enterprise-analytics/tat",
    "/enterprise-analytics/rejections",
    "/enterprise-analytics/critical",
    "/enterprise-analytics/ai",
    "/enterprise-analytics/integrations",
    "/enterprise-analytics/export",
)

API_ROUTES = (
    "/api/v1/enterprise-analytics/dashboard",
    "/api/v1/enterprise-analytics/revenue",
    "/api/v1/enterprise-analytics/lab-sla",
    "/api/v1/enterprise-analytics/collector-sla",
    "/api/v1/enterprise-analytics/partners",
    "/api/v1/enterprise-analytics/turnaround-time",
    "/api/v1/enterprise-analytics/rejections",
    "/api/v1/enterprise-analytics/critical-results",
    "/api/v1/enterprise-analytics/ai-usage",
    "/api/v1/enterprise-analytics/integration-failures",
    "/api/v1/enterprise-analytics/export",
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

    os.environ.setdefault("REPORTING_SEED_ORDERS", "50")
    os.environ.setdefault("REPORTING_SEED_TESTS", "200")
    os.environ.setdefault("REPORTING_SEED_COLLECTORS", "20")
    os.environ.setdefault("REPORTING_SEED_PARTNERS", "25")

    print("\n=== DXCON ENTERPRISE ANALYTICS VERIFY ===\n")
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
                    email="verify-analytics@demo.dxcon.test",
                    role="ADMIN",
                    password_hash=hash_password("DemoPass123!"),
                    is_active=True,
                )
            )
            db.session.commit()

        from scripts.seed_reporting_demo import seed_reporting_demo

        seed_reporting_demo()

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
        checks["enterprise_analytics_dashboard"] = {"ok": web_ok, "routes": web_results}

        api_ok = True
        api_results = {}
        for route in API_ROUTES:
            response = client.get(route, follow_redirects=True)
            ok = response.status_code == 200
            api_ok = api_ok and ok
            api_results[route] = {"status_code": response.status_code, "ok": ok}
        checks["api_endpoints"] = {"ok": api_ok, "routes": api_results}

        from app.services.enterprise_analytics_service import FEATURES, dashboard_payload

        dashboard = dashboard_payload()
        checks["feature_coverage"] = {
            "ok": len(dashboard.get("features", [])) == 11 and list(FEATURES) == dashboard.get("features"),
            "features": len(FEATURES),
        }

        revenue = _api_json(client.get("/api/v1/enterprise-analytics/revenue"))
        checks["revenue_analytics"] = {
            "ok": revenue.get("read_only") is True and "gross_revenue" in revenue,
        }

        lab_sla = _api_json(client.get("/api/v1/enterprise-analytics/lab-sla"))
        checks["lab_sla_analytics"] = {
            "ok": lab_sla.get("read_only") is True and "period_summary" in lab_sla,
        }

        collector_sla = _api_json(client.get("/api/v1/enterprise-analytics/collector-sla"))
        checks["collector_sla_analytics"] = {
            "ok": collector_sla.get("read_only") is True and "collectors" in collector_sla,
        }

        partners = _api_json(client.get("/api/v1/enterprise-analytics/partners"))
        checks["partner_performance"] = {
            "ok": partners.get("read_only") is True and "partners" in partners,
        }

        tat = _api_json(client.get("/api/v1/enterprise-analytics/turnaround-time"))
        checks["turnaround_time_analytics"] = {
            "ok": tat.get("read_only") is True and "average_tat_hours" in tat,
        }

        rejections = _api_json(client.get("/api/v1/enterprise-analytics/rejections"))
        checks["sample_rejection_analytics"] = {
            "ok": rejections.get("read_only") is True and "rejections" in rejections,
        }

        critical = _api_json(client.get("/api/v1/enterprise-analytics/critical-results"))
        checks["critical_result_analytics"] = {
            "ok": critical.get("read_only") is True and "critical_items" in critical,
        }

        ai = _api_json(client.get("/api/v1/enterprise-analytics/ai-usage"))
        checks["ai_usage_analytics"] = {
            "ok": ai.get("read_only") is True and "usage" in ai,
        }

        integration = _api_json(client.get("/api/v1/enterprise-analytics/integration-failures"))
        checks["integration_failure_analytics"] = {
            "ok": integration.get("read_only") is True and "dead_letters" in integration,
        }

        export_json = _api_json(client.get("/api/v1/enterprise-analytics/export"))
        checks["executive_kpi_export"] = {
            "ok": export_json.get("read_only") is True and "revenue" in export_json and "partners" in export_json,
        }

        export_csv = client.get("/api/v1/enterprise-analytics/export?format=csv")
        checks["executive_kpi_export_csv"] = {
            "ok": export_csv.status_code == 200 and "section,metric,value" in export_csv.get_data(as_text=True),
        }

        legacy = client.get("/api/v1/reports/revenue")
        checks["existing_reporting_api_preserved"] = {
            "ok": legacy.status_code == 200 and _api_json(legacy).get("report") == "revenue_summary",
        }

    passed = sum(1 for item in checks.values() if item.get("ok"))
    total = len(checks)
    score = round((passed / total) * 100, 1) if total else 0.0
    report = {
        "generated_at": utc_now(),
        "phase": "4.6",
        "sprint": "Enterprise Analytics Expansion",
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

    print(f"Enterprise Analytics score: {score}%")
    print(f"Checks passed: {passed}/{total}")
    print(f"Report: {REPORT_PATH}")
    if report["summary"]["ok"]:
        print("ENTERPRISE ANALYTICS VERIFY PASS\n")
        return 0
    print("ENTERPRISE ANALYTICS VERIFY FAIL\n")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
