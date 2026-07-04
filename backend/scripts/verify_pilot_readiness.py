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
REPORT_PATH = ROOT / "generated_release" / "PILOT_READINESS_REPORT.json"

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

HEALTH_ROUTES = ("/health", "/ready")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def main() -> int:
    sys.path.insert(0, str(ROOT))
    if not os.getenv("DATABASE_URL"):
        print("FAIL: DATABASE_URL is required", file=sys.stderr)
        return 1

    print("\n=== DXCON PILOT READINESS VERIFY ===\n")
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
            response = client.get(route, follow_redirects=True)
            route_ok = response.status_code == 200 and len(response.get_data(as_text=True)) > 100
            pages_ok = pages_ok and route_ok
            page_results[route] = {
                "status_code": response.status_code,
                "ok": route_ok,
            }
            if not route_ok:
                failed_routes.append(route)
        checks["dashboard_pages"] = {"ok": pages_ok, "routes": page_results}

        critical = ("/crm-pipeline", "/logistics")
        critical_results = {route: page_results.get(route, {"ok": False}) for route in critical}
        checks["critical_dashboards"] = {
            "ok": all(item.get("ok") for item in critical_results.values()),
            "routes": critical_results,
        }

    passed = sum(1 for item in checks.values() if item.get("ok"))
    total = len(checks)
    score = round((passed / total) * 100, 1) if total else 0.0
    report = {
        "generated_at": utc_now(),
        "summary": {
            "pilot_readiness_score": score,
            "checks_passed": passed,
            "checks_total": total,
            "ok": passed == total,
            "failed_routes": sorted(set(failed_routes)),
            "runtime_seconds": round(time.perf_counter() - start, 3),
        },
        "checks": checks,
    }
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")

    print(f"Pilot readiness score: {score}%")
    print(f"Checks passed: {passed}/{total}")
    print(f"Demo users: {checks['seed_data']['counts']['users']}")
    print(f"Demo patients: {checks['seed_data']['counts']['patients']}")
    print(f"Demo orders: {checks['seed_data']['counts']['orders']}")
    print(f"Report: {REPORT_PATH}")
    if failed_routes:
        print("Failed routes:", ", ".join(sorted(set(failed_routes))))
    print()
    if report["summary"]["ok"]:
        print("PILOT READINESS VERIFY PASS\n")
        return 0
    print("PILOT READINESS VERIFY FAIL\n")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
