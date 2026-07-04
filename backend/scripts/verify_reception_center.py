#!/usr/bin/env python3
"""Verify Reception Center Sprint 2.1 routes, API, and operations."""

from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = ROOT / "generated_release" / "RECEPTION_CENTER_REPORT.json"

WEB_ROUTES = (
    "/reception",
    "/reception/search",
    "/reception/register/quick",
    "/reception/register/walk-in",
    "/reception/check-in",
    "/reception/activity",
    "/reception/kpi",
)

API_ROUTES = (
    "/api/v1/reception/dashboard",
    "/api/v1/reception/search?name=demo",
    "/api/v1/reception/kpi",
    "/api/v1/reception/activity",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _login_reception(client):
    from app.models.user import User

    user = User.query.filter(User.role == "RECEPTION").first()
    if not user:
        user = User.query.filter_by(email="demo-superadmin@demo.dxcon.test").first()
    if not user:
        return False
    with client.session_transaction() as sess:
        sess["user_id"] = user.id
        sess["role"] = user.role
        sess["email"] = user.email
    return True


def main() -> int:
    sys.path.insert(0, str(ROOT))
    if not os.getenv("DATABASE_URL"):
        print("FAIL: DATABASE_URL is required", file=sys.stderr)
        return 1

    print("\n=== DXCON RECEPTION CENTER VERIFY ===\n")
    start = time.perf_counter()
    checks: dict[str, dict] = {}

    from app import create_app

    app = create_app()
    with app.app_context():
        routes = {str(rule.rule) for rule in app.url_map.iter_rules()}
        missing = [route for route in WEB_ROUTES if route not in routes]
        checks["route_registry"] = {"ok": not missing, "missing": missing}

        client = app.test_client()
        if not _login_reception(client):
            checks["auth"] = {"ok": False, "reason": "no reception user"}
        else:
            checks["auth"] = {"ok": True}

        web_results = {}
        web_ok = True
        for route in WEB_ROUTES:
            response = client.get(route, follow_redirects=True)
            ok = response.status_code == 200 and len(response.get_data(as_text=True)) > 200
            web_ok = web_ok and ok
            web_results[route] = {"status_code": response.status_code, "ok": ok}
        checks["web_pages"] = {"ok": web_ok, "routes": web_results}

        api_results = {}
        api_ok = True
        for route in API_ROUTES:
            response = client.get(route, follow_redirects=True)
            ok = response.status_code == 200
            api_ok = api_ok and ok
            api_results[route] = {"status_code": response.status_code, "ok": ok}
        checks["api_endpoints"] = {"ok": api_ok, "routes": api_results}

        from app.services.reception_service import get_kpis, next_queue_number, search_patients

        number, seq = next_queue_number()
        kpis = get_kpis()
        checks["queue_generator"] = {
            "ok": bool(number) and seq >= 1,
            "sample_number": number,
            "sequence": seq,
        }
        checks["kpis"] = {"ok": "waiting_queue" in kpis, "metrics": kpis}
        checks["patient_search"] = {
            "ok": isinstance(search_patients(name="Demo"), list),
        }

    passed = sum(1 for item in checks.values() if item.get("ok"))
    total = len(checks)
    score = round((passed / total) * 100, 1) if total else 0.0
    report = {
        "generated_at": utc_now(),
        "phase": "2.1",
        "sprint": "Reception Center",
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

    print(f"Reception Center score: {score}%")
    print(f"Checks passed: {passed}/{total}")
    print(f"Report: {REPORT_PATH}")
    if report["summary"]["ok"]:
        print("RECEPTION CENTER VERIFY PASS\n")
        return 0
    print("RECEPTION CENTER VERIFY FAIL\n")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
