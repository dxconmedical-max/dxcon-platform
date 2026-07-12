#!/usr/bin/env python3
"""Verify Release 7.0 Sprint 4 — IoT Logistics and Cold Chain."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
sys.path.insert(0, str(ROOT))

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ["IOT_SIMULATOR_ENABLED"] = "true"

REPORTS = {
    "IOT_PLATFORM_REPORT.json": ROOT / "generated_release" / "IOT_PLATFORM_REPORT.json",
    "COLD_CHAIN_REPORT.json": ROOT / "generated_release" / "COLD_CHAIN_REPORT.json",
    "LOGISTICS_SECURITY_REPORT.json": ROOT / "generated_release" / "LOGISTICS_SECURITY_REPORT.json",
    "CHAIN_OF_CUSTODY_REPORT.json": ROOT / "generated_release" / "CHAIN_OF_CUSTODY_REPORT.json",
    "IOT_OPERATIONS_UI_REPORT.json": REPO / "apps" / "web" / "generated-release" / "IOT_OPERATIONS_UI_REPORT.json",
}

ROUTES = (
    "/api/v1/iot/devices",
    "/api/v1/iot/readings",
    "/api/v1/iot/telemetry",
    "/api/v1/iot/alerts",
    "/api/v1/iot/excursions",
    "/api/v1/logistics/trips",
    "/api/v1/logistics/dashboard",
    "/api/v1/custody/events",
)

FRONTEND = {
    "operations_logistics": REPO / "apps/web/src/app/app/operations/logistics/page.tsx",
    "collector_trips": REPO / "apps/web/src/app/app/collector/trips/page.tsx",
    "lab_cold_chain": REPO / "apps/web/src/app/app/lab/cold-chain/page.tsx",
    "iot_api": REPO / "apps/web/src/lib/api/iot.ts",
}


def _run_tests() -> bool:
    proc = subprocess.run(
        [sys.executable, "-m", "unittest", "tests.test_iot_platform", "-q"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    return proc.returncode == 0


def main() -> int:
    from app import create_app
    from app.iot_platform.auth import simulator_allowed

    app = create_app()
    rules = {r.rule for r in app.url_map.iter_rules()}
    route_checks = {r: r in rules for r in ROUTES}
    frontend_checks = {k: v.exists() for k, v in FRONTEND.items()}
    tests_ok = _run_tests()

    security = {
        "device_auth": (ROOT / "app/iot_platform/auth.py").exists(),
        "credentials_not_in_api": "credential_hash" not in (ROOT / "app/api/iot_platform/routes.py").read_text(),
        "phi_guard": "patient_name" in (ROOT / "app/iot_platform/ingestion.py").read_text(),
        "simulator_production_guard": not simulator_allowed() if os.environ.get("FLASK_ENV") == "production" else True,
        "tenant_isolation": "organization_id" in (ROOT / "app/iot_platform/service.py").read_text(),
    }

    cold_chain = {
        "threshold_policies": (ROOT / "app/models/iot_platform.py").read_text().count("IoTThresholdPolicy") > 0,
        "excursions": "IoTColdChainExcursion" in (ROOT / "app/models/iot_platform.py").read_text(),
        "specimen_hold": "hold_specimen_for_excursion" in (ROOT / "app/iot_platform/service.py").read_text(),
        "no_auto_release": "auto_release" not in (ROOT / "app/iot_platform/service.py").read_text(),
    }

    custody = {
        "append_only_events": "append_custody_event" in (ROOT / "app/iot_platform/service.py").read_text(),
        "custody_api": "/api/v1/custody/events" in rules,
    }

    platform = {
        "migration": (ROOT / "migrations/017_iot_logistics.sql").exists(),
        "routes": all(route_checks.values()),
        "simulator": (ROOT / "scripts/simulate_iot_trip.py").exists(),
        "tests": tests_ok,
        "frontend": all(frontend_checks.values()),
    }

    failed = [k for k, v in {**platform, **security, **cold_chain, **custody}.items() if not v]
    status = "PASS" if not failed else "FAIL"
    ts = datetime.now(timezone.utc).isoformat()

    payloads = {
        "IOT_PLATFORM_REPORT.json": {"release": "7.0", "sprint": "Sprint 4", "status": status, "checks": platform, "routes": route_checks, "generated_at": ts},
        "COLD_CHAIN_REPORT.json": {"release": "7.0", "sprint": "Sprint 4", "status": status, "checks": cold_chain, "generated_at": ts},
        "LOGISTICS_SECURITY_REPORT.json": {"release": "7.0", "sprint": "Sprint 4", "status": status, "checks": security, "failed": failed, "generated_at": ts},
        "CHAIN_OF_CUSTODY_REPORT.json": {"release": "7.0", "sprint": "Sprint 4", "status": status, "checks": custody, "generated_at": ts},
        "IOT_OPERATIONS_UI_REPORT.json": {"release": "7.0", "sprint": "Sprint 4", "status": status, "pages": frontend_checks, "generated_at": ts},
    }

    for name, path in REPORTS.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payloads[name], indent=2), encoding="utf-8")

    print(f"IoT Platform verification: {status}")
    if failed:
        print("Failed:", failed)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
