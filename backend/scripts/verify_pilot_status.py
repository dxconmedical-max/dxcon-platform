#!/usr/bin/env python3
"""Verify Pilot Status Phase 5 Sprint 5.6."""

from __future__ import annotations

import json
import os
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = ROOT / "generated_release" / "PILOT_STATUS_REPORT.json"

WEB_ROUTES = (
    "/pilot-status",
    "/pilot-status/clinics",
    "/pilot-status/labs",
    "/pilot-status/collectors",
    "/pilot-status/doctors",
    "/pilot-status/orders",
    "/pilot-status/revenue",
    "/pilot-status/alerts",
)

API_ROUTES = (
    "/api/v1/pilot-status/dashboard",
    "/api/v1/pilot-status/overview",
    "/api/v1/pilot-status/clinics",
    "/api/v1/pilot-status/labs",
    "/api/v1/pilot-status/collectors",
    "/api/v1/pilot-status/doctors",
    "/api/v1/pilot-status/orders",
    "/api/v1/pilot-status/revenue",
    "/api/v1/pilot-status/alerts",
    "/api/v1/pilot-status/inventory",
    "/api/v1/pilot-status/readiness",
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


def _seed_pilot_snapshot():
    from app.core.passwords import hash_password
    from app.extensions.db import db
    from app.models.alert import Alert
    from app.models.clinic_profile import ClinicProfile
    from app.models.driver import Driver
    from app.models.laboratory import Laboratory
    from app.models.order import Order
    from app.models.user import User

    if not ClinicProfile.query.first():
        db.session.add(
            ClinicProfile(
                clinic_id=str(uuid.uuid4()),
                clinic_code="PILOT-CLN-001",
                name="Pilot Clinic Alpha",
                status="ACTIVE",
            )
        )
    if not Laboratory.query.first():
        db.session.add(
            Laboratory(
                code="PILOT-LAB-001",
                name="Pilot Laboratory",
                is_active=True,
            )
        )
    if not Driver.query.first():
        db.session.add(
            Driver(
                driver_code="PILOT-COL-001",
                full_name="Pilot Collector",
                status="ACTIVE",
                ops_status="ACTIVE",
            )
        )
    if not User.query.filter_by(role="DOCTOR").first():
        db.session.add(
            User(
                email="pilot-doctor@demo.dxcon.test",
                role="DOCTOR",
                password_hash=hash_password("DemoPass123!"),
                is_active=True,
            )
        )
    if not Order.query.first():
        db.session.add(
            Order(
                order_code="PILOT-ORD-001",
                patient_id=str(uuid.uuid4()),
                status="PENDING",
                total_amount=250000,
            )
        )
    if not Alert.query.filter_by(status="OPEN").first():
        db.session.add(
            Alert(
                alert_code=f"PILOT-ALR-{uuid.uuid4().hex[:6].upper()}",
                alert_type="OPERATIONS",
                severity="MEDIUM",
                message="Pilot alert sample",
                status="OPEN",
            )
        )
    db.session.commit()


def main() -> int:
    sys.path.insert(0, str(ROOT))
    if not os.getenv("DATABASE_URL"):
        print("FAIL: DATABASE_URL is required", file=sys.stderr)
        return 1

    print("\n=== DXCON PILOT STATUS VERIFY ===\n")
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
                    email="verify-pilot@demo.dxcon.test",
                    role="ADMIN",
                    password_hash=hash_password("DemoPass123!"),
                    is_active=True,
                )
            )
            db.session.commit()

        _seed_pilot_snapshot()

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
        checks["pilot_status"] = {"ok": web_ok, "routes": web_results}

        api_ok = True
        api_results = {}
        for route in API_ROUTES:
            response = client.get(route, follow_redirects=True)
            ok = response.status_code == 200
            api_ok = api_ok and ok
            api_results[route] = {"status_code": response.status_code, "ok": ok}
        checks["api_endpoints"] = {"ok": api_ok, "routes": api_results}

        from app.services.pilot_status_service import FEATURES

        dashboard = _api_json(client.get("/api/v1/pilot-status/dashboard"))
        checks["feature_coverage"] = {
            "ok": len(dashboard.get("features", [])) == 8 and list(FEATURES) == dashboard.get("features"),
            "features": len(FEATURES),
        }

        overview = _api_json(client.get("/api/v1/pilot-status/overview"))
        checks["pilot_status_overview"] = {"ok": overview.get("status") in {"OK", "WARN"}}

        checks["active_clinics"] = {
            "ok": _api_json(client.get("/api/v1/pilot-status/clinics")).get("count", 0) >= 1,
        }
        checks["active_labs"] = {
            "ok": _api_json(client.get("/api/v1/pilot-status/labs")).get("count", 0) >= 1,
        }
        checks["collectors_online"] = {
            "ok": _api_json(client.get("/api/v1/pilot-status/collectors")).get("count", 0) >= 1,
        }
        checks["doctors_online"] = {
            "ok": _api_json(client.get("/api/v1/pilot-status/doctors")).get("count", 0) >= 1,
        }
        checks["todays_orders"] = {
            "ok": _api_json(client.get("/api/v1/pilot-status/orders")).get("count", 0) >= 1,
        }
        checks["todays_revenue"] = {
            "ok": "amount" in _api_json(client.get("/api/v1/pilot-status/revenue")),
        }
        checks["alerts"] = {
            "ok": _api_json(client.get("/api/v1/pilot-status/alerts")).get("open_count", 0) >= 1,
        }

        legacy_exec = client.get("/executive-v9", follow_redirects=True)
        checks["legacy_executive_preserved"] = {"ok": legacy_exec.status_code == 200}

        legacy_dashboard = _api_json(client.get("/api/v1/dashboard/summary"))
        checks["legacy_dashboard_api_preserved"] = {
            "ok": "orders" in legacy_dashboard,
        }

        legacy_checklist = client.get("/pilot-checklist", follow_redirects=True)
        checks["legacy_pilot_checklist_preserved"] = {"ok": legacy_checklist.status_code == 200}

    passed = sum(1 for item in checks.values() if item.get("ok"))
    total = len(checks)
    score = round((passed / total) * 100, 1) if total else 0.0
    report = {
        "generated_at": utc_now(),
        "phase": "5.6",
        "sprint": "Pilot Status",
        "summary": {
            "score": score,
            "checks_passed": passed,
            "checks_total": total,
            "ok": passed == total,
            "runtime_seconds": round(time.perf_counter() - start, 3),
        },
        "checks": checks,
        "readiness": _api_json(client.get("/api/v1/pilot-status/readiness")) if "client" in locals() else {},
    }
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")

    print(f"Pilot Status score: {score}%")
    print(f"Checks passed: {passed}/{total}")
    print(f"Report: {REPORT_PATH}")
    if report["summary"]["ok"]:
        print("PILOT STATUS VERIFY PASS\n")
        return 0
    print("PILOT STATUS VERIFY FAIL\n")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
