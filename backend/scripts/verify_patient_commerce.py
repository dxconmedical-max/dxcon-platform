#!/usr/bin/env python3
"""Verify Release 8.0 Sprint 7 — Patient Commerce."""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "generated_release" / "SPRINT_7_PATIENT_COMMERCE_REPORT.json"

CHECKS = {
    "slot_engine": ROOT / "app/patient_marketplace/slot_engine.py",
    "home_collection": ROOT / "app/patient_marketplace/home_collection.py",
    "migration": ROOT / "migrations/020_patient_commerce.sql",
    "tests": ROOT / "tests/test_patient_commerce.py",
    "routes": ROOT / "app/patient_marketplace/routes.py",
}

FRONTEND = {
    "services_page": ROOT.parent / "apps/web/src/app/services/page.tsx",
    "packages_page": ROOT.parent / "apps/web/src/app/packages/page.tsx",
    "partners_page": ROOT.parent / "apps/web/src/app/partners/page.tsx",
    "booking_wizard": ROOT.parent / "apps/web/src/components/workspace/PatientCommerceBookingWizard.tsx",
    "marketplace_api": ROOT.parent / "apps/web/src/lib/api/marketplace.ts",
}


def _run_tests() -> bool:
    proc = subprocess.run(
        [sys.executable, "-m", "unittest", "tests.test_patient_commerce", "-v"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    return proc.returncode == 0


def main() -> int:
    results = {name: path.exists() for name, path in CHECKS.items()}
    frontend = {name: path.exists() for name, path in FRONTEND.items()}
    routes_text = CHECKS["routes"].read_text(encoding="utf-8") if CHECKS["routes"].exists() else ""
    results["public_catalog_routes"] = "/public/services" in routes_text and "/public/partners" in routes_text
    results["slot_hold_route"] = "/slots/hold" in routes_text
    results["quotation_route"] = "/catalog/quote" in routes_text
    results["frontend"] = all(frontend.values())
    results["unit_tests"] = _run_tests() if CHECKS["tests"].exists() else False
    failed = [k for k, v in results.items() if not v]
    status = "PASS" if not failed else "FAIL"
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "release": "8.0",
        "sprint": "Sprint 7 — Patient Commerce",
        "status": status,
        "checks": results,
        "frontend_checks": frontend,
        "failed": failed,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Patient commerce verification: {status}")
    if failed:
        print("Failed:", failed)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
