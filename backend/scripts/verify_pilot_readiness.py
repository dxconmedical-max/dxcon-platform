#!/usr/bin/env python3
"""Verify pilot readiness routes, dashboards, seed data, and health probes."""

from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = ROOT / "generated_release"
PILOT_REPORT = REPORT_DIR / "PILOT_READINESS_REPORT.json"
DASHBOARD_REPORT = REPORT_DIR / "DASHBOARD_STATUS.json"
WORKFLOW_REPORT = REPORT_DIR / "WORKFLOW_STATUS.json"

REQUIRED_ROUTES = (
    "/",
    "/health",
    "/ready",
    "/executive",
    "/executive-v9",
    "/crm-pipeline",
    "/logistics",
    "/reception",
    "/doctor-workbench",
    "/doctor/dashboard",
    "/patient-portal",
    "/patient/demo",
    "/demo-accounts",
    "/workflow-demo",
    "/pilot-checklist",
)

PAGE_ROUTES = (
    "/",
    "/executive-v9",
    "/crm-pipeline",
    "/logistics",
    "/reception",
    "/doctor-workbench",
    "/patient-portal",
    "/demo-accounts",
    "/workflow-demo",
    "/pilot-checklist",
)

DASHBOARD_ROUTES = {
    "executive": "/executive-v9",
    "crm": "/crm-pipeline",
    "logistics": "/logistics",
    "reception": "/reception",
    "doctor_workbench": "/doctor-workbench",
    "patient_portal": "/patient-portal",
}

WORKFLOW_ROUTES = (
    "/workflow-demo",
    "/reception",
    "/orders/new",
    "/logistics",
    "/lab-operations",
    "/doctor-workbench",
    "/patient-portal",
    "/notifications",
)

HEALTH_ROUTES = ("/health", "/ready")
DEMO_LOGIN = ("demo-superadmin@demo.dxcon.test", "DemoPass123!")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _login_session(client, *, role: str | None = None) -> bool:
    with client.session_transaction() as sess:
        from app.models.user import User

        user = None
        if role:
            user = User.query.filter_by(role=role).first()
        if not user:
            user = User.query.filter_by(email=DEMO_LOGIN[0]).first()
        if not user:
            return False
        sess["user_id"] = user.id
        sess["role"] = user.role
        sess["email"] = user.email
    return True


def _page_ok(client, route: str, *, login: bool = False) -> dict:
    if login:
        with client.session_transaction() as sess:
            from app.models.user import User

            user = User.query.filter_by(email=DEMO_LOGIN[0]).first()
            if user:
                sess["user_id"] = user.id
                sess["role"] = user.role
                sess["email"] = user.email
    response = client.get(route, follow_redirects=True)
    body = response.get_data(as_text=True)
    ok = response.status_code == 200 and len(body) > 100
    if login and route == "/executive":
        ok = ok and "Executive Dashboard" in body
    if route == "/reception":
        ok = ok and "Reception Center" in body
    return {"status_code": response.status_code, "ok": ok, "bytes": len(body)}


def main() -> int:
    sys.path.insert(0, str(ROOT))
    if not os.getenv("DATABASE_URL"):
        print("FAIL: DATABASE_URL is required", file=sys.stderr)
        return 1

    print("\n=== DXCON PILOT PHASE 3A READINESS VERIFY ===\n")
    start = time.perf_counter()
    checks: dict[str, dict] = {}
    failed_routes: list[str] = []

    from app import create_app

    app = create_app()
    with app.app_context():
        from app.web.demo_pilot_lib import seeded_summary

        summary = seeded_summary()
        checks["seed_data"] = {
            "ok": summary["users"] > 0 and summary["patients"] > 0 and summary["orders"] > 0,
            "counts": summary,
        }

        routes = {str(rule.rule) for rule in app.url_map.iter_rules()}
        missing = [route for route in REQUIRED_ROUTES if route not in routes]
        checks["route_registry"] = {
            "ok": not missing,
            "required": list(REQUIRED_ROUTES),
            "missing": missing,
        }

        client = app.test_client()
        health_results = {}
        health_ok = True
        for route in HEALTH_ROUTES:
            response = client.get(route)
            payload = response.get_json() or {}
            route_ok = response.status_code == 200
            health_ok = health_ok and route_ok
            health_results[route] = {
                "status_code": response.status_code,
                "payload": payload,
                "ok": route_ok,
            }
            if not route_ok:
                failed_routes.append(route)
        checks["health_endpoints"] = {"ok": health_ok, "routes": health_results}

        page_results = {}
        pages_ok = True
        for route in PAGE_ROUTES:
            if route == "/reception":
                _login_session(client, role="RECEPTION")
            result = _page_ok(client, route)
            page_results[route] = result
            pages_ok = pages_ok and result["ok"]
            if not result["ok"]:
                failed_routes.append(route)

        executive_result = _page_ok(client, "/executive", login=True)
        page_results["/executive"] = executive_result
        pages_ok = pages_ok and executive_result["ok"]
        if not executive_result["ok"]:
            failed_routes.append("/executive")

        checks["dashboard_pages"] = {"ok": pages_ok, "routes": page_results}

        critical = ("/crm-pipeline", "/logistics", "/reception", "/doctor-workbench", "/patient-portal")
        critical_results = {route: page_results.get(route, {"ok": False}) for route in critical}
        checks["critical_dashboards"] = {
            "ok": all(item.get("ok") for item in critical_results.values()),
            "routes": critical_results,
        }

        dashboard_status = {}
        for name, route in DASHBOARD_ROUTES.items():
            result = page_results.get(route, _page_ok(client, route))
            dashboard_status[name] = {
                "route": route,
                "ok": result.get("ok", False),
                "status_code": result.get("status_code"),
            }

        workflow_status = {}
        for route in WORKFLOW_ROUTES:
            if route not in routes:
                workflow_status[route] = {"ok": False, "reason": "not_registered"}
                continue
            if route == "/reception":
                _login_session(client, role="RECEPTION")
            result = _page_ok(client, route)
            workflow_status[route] = result
            if not result["ok"]:
                failed_routes.append(route)

    passed = sum(1 for item in checks.values() if item.get("ok"))
    total = len(checks)
    score = round((passed / total) * 100, 1) if total else 0.0
    runtime = round(time.perf_counter() - start, 3)

    summary_block = {
        "pilot_readiness_score": score,
        "checks_passed": passed,
        "checks_total": total,
        "ok": passed == total and all(v.get("ok") for v in dashboard_status.values()),
        "failed_routes": sorted(set(failed_routes)),
        "runtime_seconds": runtime,
        "phase": "3A",
    }

    pilot_report = {
        "generated_at": utc_now(),
        "summary": summary_block,
        "checks": checks,
    }
    dashboard_report = {
        "generated_at": utc_now(),
        "phase": "3A",
        "dashboards": dashboard_status,
        "score": round(
            sum(1 for item in dashboard_status.values() if item.get("ok")) / max(len(dashboard_status), 1) * 100,
            1,
        ),
    }
    workflow_report = {
        "generated_at": utc_now(),
        "phase": "3A",
        "routes": workflow_status,
        "score": round(
            sum(1 for item in workflow_status.values() if item.get("ok")) / max(len(workflow_status), 1) * 100,
            1,
        ),
    }

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    PILOT_REPORT.write_text(json.dumps(pilot_report, indent=2, default=str), encoding="utf-8")
    DASHBOARD_REPORT.write_text(json.dumps(dashboard_report, indent=2, default=str), encoding="utf-8")
    WORKFLOW_REPORT.write_text(json.dumps(workflow_report, indent=2, default=str), encoding="utf-8")

    print(f"Pilot readiness score: {score}%")
    print(f"Dashboard score: {dashboard_report['score']}%")
    print(f"Workflow score: {workflow_report['score']}%")
    print(f"Checks passed: {passed}/{total}")
    print(f"Demo users: {checks['seed_data']['counts']['users']}")
    print(f"Demo patients: {checks['seed_data']['counts']['patients']}")
    print(f"Demo orders: {checks['seed_data']['counts']['orders']}")
    print(f"Reports: {PILOT_REPORT}, {DASHBOARD_REPORT}, {WORKFLOW_REPORT}")
    if failed_routes:
        print("Failed routes:", ", ".join(sorted(set(failed_routes))))
    print()
    if summary_block["ok"]:
        print("PILOT PHASE 3A READINESS VERIFY PASS\n")
        return 0
    print("PILOT PHASE 3A READINESS VERIFY FAIL\n")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
