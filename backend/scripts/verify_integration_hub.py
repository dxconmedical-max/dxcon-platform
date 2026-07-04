#!/usr/bin/env python3
"""Verify Integration Hub Phase 4 Sprint 4.1 routes, API, and operations."""

from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = ROOT / "generated_release" / "INTEGRATION_HUB_REPORT.json"

WEB_ROUTES = (
    "/integration-hub",
    "/integration-hub/connectors",
    "/integration-hub/adapters",
    "/integration-hub/webhooks",
    "/integration-hub/api-keys",
    "/integration-hub/retry-queue",
    "/integration-hub/dead-letters",
    "/integration-hub/audit",
    "/integration-hub/sandbox",
)

API_ROUTES = (
    "/api/v1/integration-hub/dashboard",
    "/api/v1/integration-hub/connectors",
    "/api/v1/integration-hub/adapters",
    "/api/v1/integration-hub/webhooks",
    "/api/v1/integration-hub/api-keys",
    "/api/v1/integration-hub/retry-queue",
    "/api/v1/integration-hub/dead-letters",
    "/api/v1/integration-hub/audit",
)

REQUIRED_ADAPTERS = ("HIS", "LIS", "EMR", "ERP", "INSURANCE", "PAYMENT")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _login_admin(client):
    from app.models.user import User

    user = User.query.filter(User.role == "SUPER_ADMIN").first()
    if not user:
        user = User.query.filter_by(email="demo-superadmin@demo.dxcon.test").first()
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

    print("\n=== DXCON INTEGRATION HUB VERIFY ===\n")
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
                    email="verify-admin@demo.dxcon.test",
                    role="ADMIN",
                    password_hash=hash_password("DemoPass123!"),
                    is_active=True,
                )
            )
            db.session.commit()

        routes = {str(rule.rule) for rule in app.url_map.iter_rules()}
        missing = [route for route in WEB_ROUTES if route not in routes]
        api_missing = [route for route in API_ROUTES if route not in routes]
        checks["route_registry"] = {
            "ok": not missing and not api_missing,
            "missing_web": missing,
            "missing_api": api_missing,
        }

        client = app.test_client()
        if not _login_admin(client):
            checks["auth"] = {"ok": False, "reason": "no admin user"}
        else:
            checks["auth"] = {"ok": True}

        web_results = {}
        web_ok = True
        for route in WEB_ROUTES:
            response = client.get(route, follow_redirects=True)
            ok = response.status_code == 200 and len(response.get_data(as_text=True)) > 200
            web_ok = web_ok and ok
            web_results[route] = {"status_code": response.status_code, "ok": ok}
        checks["integration_center_dashboard"] = {"ok": web_ok, "routes": web_results}

        api_results = {}
        api_ok = True
        for route in API_ROUTES:
            response = client.get(route, follow_redirects=True)
            ok = response.status_code == 200
            api_ok = api_ok and ok
            api_results[route] = {"status_code": response.status_code, "ok": ok}
        checks["api_endpoints"] = {"ok": api_ok, "routes": api_results}

        from app.services.integration_hub_service import (
            SUPPORTED_ADAPTERS,
            dashboard_payload,
            list_adapters,
            list_connectors,
            sandbox_test,
        )

        dashboard = dashboard_payload()
        checks["connector_registry"] = {
            "ok": list_connectors()["count"] >= 1,
            "count": list_connectors()["count"],
        }
        adapter_types = {item["type"] for item in list_adapters()["adapters"]}
        missing_adapters = [t for t in REQUIRED_ADAPTERS if t not in adapter_types]
        checks["adapter_registry"] = {
            "ok": not missing_adapters,
            "adapters": sorted(adapter_types),
            "missing": missing_adapters,
        }
        webhook_payload = _api_json(client.get("/api/v1/integration-hub/webhooks"))
        checks["webhook_manager"] = {"ok": "webhooks" in webhook_payload}
        api_keys_payload = _api_json(client.get("/api/v1/integration-hub/api-keys"))
        checks["api_key_manager"] = {"ok": "keys" in api_keys_payload}
        retry_payload = _api_json(client.get("/api/v1/integration-hub/retry-queue"))
        checks["retry_queue"] = {"ok": "jobs" in retry_payload}
        dlq_payload = _api_json(client.get("/api/v1/integration-hub/dead-letters"))
        checks["dead_letter_queue"] = {"ok": "dead_letters" in dlq_payload}

        sandbox_response = client.post(
            "/api/v1/integration-hub/sandbox/test",
            json={"adapter_type": "HIS", "payload": {"patient_id": "VERIFY-001"}},
        )
        sandbox_body = _api_json(sandbox_response)
        sandbox_ok = sandbox_response.status_code == 200 and sandbox_body.get("sandbox") is True
        checks["sandbox_test_endpoint"] = {
            "ok": sandbox_ok,
            "status_code": sandbox_response.status_code,
        }

        audit_payload = _api_json(client.get("/api/v1/integration-hub/audit"))
        audit_ok = audit_payload.get("count", 0) >= 1
        checks["integration_audit_log"] = {"ok": audit_ok, "count": audit_payload.get("count", 0)}

        feature_count = len(dashboard.get("features", []))
        checks["feature_coverage"] = {
            "ok": feature_count == 15 and set(SUPPORTED_ADAPTERS) == set(REQUIRED_ADAPTERS),
            "features": feature_count,
            "supported_adapters": list(SUPPORTED_ADAPTERS),
        }

        # Exercise remaining sandbox adapters (non-destructive)
        adapter_ok = True
        adapter_results = {}
        for adapter in REQUIRED_ADAPTERS:
            try:
                result = sandbox_test(adapter, {"verify": True}, actor="verify-script")
                adapter_ok = adapter_ok and bool(result.get("result"))
                adapter_results[adapter] = {"ok": True}
            except Exception as exc:
                adapter_ok = False
                adapter_results[adapter] = {"ok": False, "error": str(exc)}
        checks["adapter_sandbox_matrix"] = {"ok": adapter_ok, "adapters": adapter_results}

    passed = sum(1 for item in checks.values() if item.get("ok"))
    total = len(checks)
    score = round((passed / total) * 100, 1) if total else 0.0
    report = {
        "generated_at": utc_now(),
        "phase": "4.1",
        "sprint": "Integration Hub",
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

    print(f"Integration Hub score: {score}%")
    print(f"Checks passed: {passed}/{total}")
    print(f"Report: {REPORT_PATH}")
    if report["summary"]["ok"]:
        print("INTEGRATION HUB VERIFY PASS\n")
        return 0
    print("INTEGRATION HUB VERIFY FAIL\n")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
