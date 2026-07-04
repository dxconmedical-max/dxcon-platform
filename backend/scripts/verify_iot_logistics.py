#!/usr/bin/env python3
"""Verify IoT Cold Chain Logistics Phase 4 Sprint 4.3."""

from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = ROOT / "generated_release" / "IOT_LOGISTICS_REPORT.json"

WEB_ROUTES = (
    "/iot-logistics",
    "/iot-logistics/devices",
    "/iot-logistics/cold-boxes",
    "/iot-logistics/adapters",
    "/iot-logistics/alerts",
    "/iot-logistics/timeline",
    "/iot-logistics/chain-of-custody",
    "/iot-logistics/offline-buffer",
    "/iot-logistics/device-health",
    "/iot-logistics/ingest",
)

API_ROUTES = (
    "/api/v1/iot-logistics/dashboard",
    "/api/v1/iot-logistics/devices",
    "/api/v1/iot-logistics/cold-boxes",
    "/api/v1/iot-logistics/adapters",
    "/api/v1/iot-logistics/alerts",
    "/api/v1/iot-logistics/chain-of-custody",
    "/api/v1/iot-logistics/offline-buffer",
    "/api/v1/iot-logistics/cold-chain/status",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _login_logistics(client):
    from app.models.user import User

    user = User.query.filter(User.role == "COLLECTOR").first()
    if not user:
        user = User.query.filter(User.role == "ADMIN").first()
    if not user:
        user = User.query.filter(User.role == "SUPER_ADMIN").first()
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

    print("\n=== DXCON IOT COLD CHAIN LOGISTICS VERIFY ===\n")
    start = time.perf_counter()
    checks: dict[str, dict] = {}

    from app import create_app

    app = create_app()
    with app.app_context():
        from app.core.passwords import hash_password
        from app.extensions.db import db
        from app.models.user import User

        db.create_all()
        if not User.query.filter(User.role.in_(("SUPER_ADMIN", "ADMIN", "COLLECTOR"))).first():
            db.session.add(
                User(
                    email="verify-collector@demo.dxcon.test",
                    role="COLLECTOR",
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
        if not _login_logistics(client):
            checks["auth"] = {"ok": False, "reason": "no logistics user"}
        else:
            checks["auth"] = {"ok": True}

        web_results = {}
        web_ok = True
        for route in WEB_ROUTES:
            response = client.get(route, follow_redirects=True)
            ok = response.status_code == 200 and len(response.get_data(as_text=True)) > 200
            web_ok = web_ok and ok
            web_results[route] = {"status_code": response.status_code, "ok": ok}
        checks["logistics_iot_dashboard"] = {"ok": web_ok, "routes": web_results}

        api_ok = True
        api_results = {}
        for route in API_ROUTES:
            response = client.get(route, follow_redirects=True)
            ok = response.status_code == 200
            api_ok = api_ok and ok
            api_results[route] = {"status_code": response.status_code, "ok": ok}
        checks["api_endpoints"] = {"ok": api_ok, "routes": api_results}

        from app.services.iot_logistics_service import FEATURES, dashboard_payload, list_adapters

        dashboard = dashboard_payload()
        device_id = _api_json(client.get("/api/v1/iot-logistics/devices"))["devices"][0]["id"]

        checks["iot_device_registry"] = {
            "ok": _api_json(client.get("/api/v1/iot-logistics/devices")).get("count", 0) >= 1
        }
        checks["cold_box_registry"] = {
            "ok": _api_json(client.get("/api/v1/iot-logistics/cold-boxes")).get("count", 0) >= 1
        }
        checks["device_adapter_pattern"] = {
            "ok": list_adapters()["count"] >= 3,
            "adapters": [item["type"] for item in list_adapters()["adapters"]],
        }

        temp = _api_json(
            client.post(
                "/api/v1/iot-logistics/ingest",
                json={
                    "adapter_type": "GENERIC",
                    "payload": {"event_type": "TEMPERATURE", "device_id": device_id, "celsius": 5.0},
                },
            )
        )
        checks["temperature_event"] = {"ok": temp.get("ingested") is True and temp.get("event_type") == "TEMPERATURE"}

        gps = _api_json(
            client.post(
                "/api/v1/iot-logistics/ingest",
                json={
                    "adapter_type": "GENERIC",
                    "payload": {
                        "event_type": "GPS",
                        "device_id": device_id,
                        "latitude": 10.77,
                        "longitude": 106.70,
                    },
                },
            )
        )
        checks["gps_event"] = {"ok": gps.get("event_type") == "GPS"}

        shock = _api_json(
            client.post(
                "/api/v1/iot-logistics/ingest",
                json={
                    "adapter_type": "GENERIC",
                    "payload": {"event_type": "SHOCK", "device_id": device_id, "g_force": 4.2},
                },
            )
        )
        checks["shock_event"] = {"ok": shock.get("event_type") == "SHOCK"}

        custody = _api_json(client.get(f"/api/v1/iot-logistics/chain-of-custody?device_id={device_id}"))
        checks["chain_of_custody"] = {"ok": custody.get("count", 0) >= 1}

        alerts = _api_json(client.get("/api/v1/iot-logistics/alerts"))
        checks["sensor_alert"] = {"ok": "alerts" in alerts}

        timeline = _api_json(client.get(f"/api/v1/iot-logistics/timeline/{device_id}"))
        checks["route_timeline"] = {"ok": timeline.get("count", 0) >= 1}

        breach = _api_json(
            client.post(
                "/api/v1/iot-logistics/temperature-breach",
                json={"device_id": device_id, "celsius": 12.0},
            )
        )
        checks["temperature_breach_detection"] = {"ok": breach.get("breach") is True}

        buffered = _api_json(
            client.post(
                "/api/v1/iot-logistics/ingest",
                json={
                    "adapter_type": "DEMO_SENSOR",
                    "offline": True,
                    "payload": {
                        "type": "TEMPERATURE",
                        "deviceId": device_id,
                        "tempC": 4.8,
                        "offline": True,
                    },
                },
            )
        )
        checks["offline_device_event_buffer"] = {"ok": buffered.get("buffered") is True}

        synced = _api_json(
            client.post(
                "/api/v1/iot-logistics/offline-buffer/sync",
                json={"device_id": device_id},
            )
        )
        checks["offline_buffer_sync"] = {"ok": synced.get("synced_count", 0) >= 1}

        health = _api_json(client.get(f"/api/v1/iot-logistics/device-health/{device_id}"))
        checks["device_health"] = {"ok": "health_score" in health}

        ingest = _api_json(
            client.post(
                "/api/v1/iot-logistics/ingest",
                json={
                    "adapter_type": "VENDOR_GATEWAY",
                    "payload": {
                        "device_id": device_id,
                        "readings": {"temperature": 6.1, "latitude": 10.1, "longitude": 106.1, "battery": 88},
                    },
                },
            )
        )
        checks["device_ingestion_api"] = {"ok": ingest.get("ingested") is True}

        checks["feature_coverage"] = {
            "ok": len(dashboard.get("features", [])) == 14 and list(FEATURES) == dashboard.get("features"),
            "features": len(FEATURES),
        }

    passed = sum(1 for item in checks.values() if item.get("ok"))
    total = len(checks)
    score = round((passed / total) * 100, 1) if total else 0.0
    report = {
        "generated_at": utc_now(),
        "phase": "4.3",
        "sprint": "IoT Cold Chain Logistics",
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

    print(f"IoT Cold Chain Logistics score: {score}%")
    print(f"Checks passed: {passed}/{total}")
    print(f"Report: {REPORT_PATH}")
    if report["summary"]["ok"]:
        print("IOT COLD CHAIN LOGISTICS VERIFY PASS\n")
        return 0
    print("IOT COLD CHAIN LOGISTICS VERIFY FAIL\n")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
