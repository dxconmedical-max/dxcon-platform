#!/usr/bin/env python3
"""Verify demo workflow counts, health probes, and dashboard routes."""

from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = ROOT / "generated_release" / "DEMO_WORKFLOW_REPORT.json"

DASHBOARD_ROUTES = (
    "/",
    "/executive-v9",
    "/crm-pipeline",
    "/logistics",
    "/reception",
    "/doctor/dashboard",
    "/patient/demo",
)

HEALTH_ROUTES = ("/health", "/ready", "/live")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def main() -> int:
    sys.path.insert(0, str(ROOT))
    if not os.getenv("DATABASE_URL"):
        print("FAIL: DATABASE_URL is required", file=sys.stderr)
        return 1

    print("\n=== DXCON DEMO WORKFLOW VERIFY ===\n")
    start = time.perf_counter()
    checks: dict[str, dict] = {}

    from app import create_app

    app = create_app()
    with app.app_context():
        from app.extensions.db import db
        from app.infrastructure.schema_introspection import table_exists_name
        from app.models.order import Order
        from app.models.order_item import OrderItem
        from app.models.patient import Patient
        from app.models.sample_collection import SampleCollection
        from app.models.test_catalog import TestCatalog
        from app.models.user import User
        from app.web.demo_pilot_lib import seeded_summary

        counts = seeded_summary()
        total_counts = {
            "users": User.query.count() if table_exists_name("users") else 0,
            "patients": Patient.query.count() if table_exists_name("patients") else 0,
            "test_catalog": TestCatalog.query.count() if table_exists_name("test_catalogs") else 0,
            "orders": Order.query.count() if table_exists_name("orders") else 0,
        }
        optional_counts = {}
        if table_exists_name("order_items"):
            optional_counts["order_items"] = OrderItem.query.count()
        if table_exists_name("sample_collections"):
            optional_counts["sample_collections"] = SampleCollection.query.count()

        checks["seeded_counts"] = {
            "ok": counts["users"] > 0 and counts["patients"] > 0 and counts["orders"] > 0,
            "demo": counts,
            "totals": total_counts,
            "optional": optional_counts,
        }

        routes = {str(rule.rule) for rule in app.url_map.iter_rules()}
        missing_dashboards = [route for route in DASHBOARD_ROUTES if route not in routes]
        checks["dashboard_routes"] = {
            "ok": not missing_dashboards,
            "required": list(DASHBOARD_ROUTES),
            "missing": missing_dashboards,
        }

        client = app.test_client()
        health_results = {}
        health_ok = True
        for route in HEALTH_ROUTES:
            response = client.get(route)
            payload = {}
            try:
                payload = response.get_json() or {}
            except Exception:
                payload = {"raw": response.get_data(as_text=True)[:200]}
            route_ok = response.status_code == 200 and payload.get("status") in {"OK", "UP", None}
            health_ok = health_ok and route_ok
            health_results[route] = {
                "status_code": response.status_code,
                "payload": payload,
                "ok": route_ok,
            }
        checks["health_endpoints"] = {"ok": health_ok, "routes": health_results}

        dashboard_results = {}
        dashboards_ok = True
        for route in DASHBOARD_ROUTES:
            response = client.get(route, follow_redirects=True)
            route_ok = response.status_code == 200 and len(response.get_data(as_text=True)) > 100
            dashboards_ok = dashboards_ok and route_ok
            dashboard_results[route] = {
                "status_code": response.status_code,
                "ok": route_ok,
            }
        checks["dashboard_pages"] = {"ok": dashboards_ok, "routes": dashboard_results}

    passed = sum(1 for item in checks.values() if item.get("ok"))
    report = {
        "generated_at": utc_now(),
        "summary": {
            "checks_passed": passed,
            "checks_total": len(checks),
            "ok": passed == len(checks),
            "runtime_seconds": round(time.perf_counter() - start, 3),
        },
        "checks": checks,
        "blockers": [
            name for name, item in checks.items() if not item.get("ok")
        ],
    }
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")

    print(f"Checks passed: {passed}/{len(checks)}")
    print(f"Demo users: {checks['seeded_counts']['demo']['users']}")
    print(f"Demo patients: {checks['seeded_counts']['demo']['patients']}")
    print(f"Demo tests: {checks['seeded_counts']['demo']['test_catalog']}")
    print(f"Demo orders: {checks['seeded_counts']['demo']['orders']}")
    print(f"Report: {REPORT_PATH}\n")
    if report["blockers"]:
        print("Blockers:", ", ".join(report["blockers"]))
        return 1
    print("DEMO WORKFLOW VERIFY PASS\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
