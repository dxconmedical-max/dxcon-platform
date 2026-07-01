#!/usr/bin/env python3
"""Go-Live Sprint Day 1 - Core Stabilization verification."""

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INVENTORY_DIR = ROOT / "inventory"
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"


def run_command(label, cmd):
    print(f"\n--- {label} ---")
    result = subprocess.run(cmd, cwd=ROOT)
    if result.returncode != 0:
        print(f"FAILED: {label}")
        return False
    print(f"OK: {label}")
    return True


def verify_inventory_files():
    print("\n--- API inventory files ---")
    required = ["api_inventory.json", "route_inventory.json", "endpoint_dependency.json"]
    errors = 0
    for name in required:
        path = INVENTORY_DIR / name
        if path.exists() and path.stat().st_size > 10:
            print("OK:", name)
        else:
            print("MISSING:", name)
            errors += 1
    return errors == 0


def verify_health_endpoints():
    print("\n--- Health endpoints ---")
    from app import create_app

    app = create_app()
    app.config["TESTING"] = True
    client = app.test_client()

    endpoints = [
        "/api/v1/system/health",
        "/api/v1/system/liveness",
        "/api/v1/system/readiness",
        "/api/v1/system/version",
        "/api/v1/system/build",
        "/api/v1/system/live",
        "/api/v1/system/ready",
    ]

    errors = 0
    for path in endpoints:
        response = client.get(path)
        if response.status_code in {200, 503}:
            print("OK:", path, response.status_code)
        else:
            print("FAIL:", path, response.status_code)
            errors += 1

    error_response = client.get("/api/v1/system/does-not-exist-go-live")
    payload = error_response.get_json() or {}
    if (
        error_response.status_code == 404
        and payload.get("success") is False
        and payload.get("request_id")
        and payload.get("timestamp")
        and payload.get("error", {}).get("code") == "NOT_FOUND"
    ):
        print("OK: standardized error envelope")
    else:
        print("FAIL: error envelope", error_response.status_code, payload)
        errors += 1

    return errors == 0


def verify_startup_checks():
    print("\n--- Startup checks ---")
    from app import create_app
    from app.core.startup_checks import run_startup_checks

    app = create_app()
    with app.app_context():
        result = run_startup_checks(app)
        names = {check["name"] for check in result["checks"]}
        required = {"storage", "jwt", "scheduler", "plugins", "smtp", "redis"}
        missing = required - names
        if missing:
            print("FAIL: missing startup checks", missing)
            return False
        failed = [c for c in result["checks"] if c["status"] == "fail"]
        if failed:
            print("FAIL: startup checks", failed)
            return False
        print("OK: startup checks", result["status"])
        return True


def main():
    print("\n=== GO-LIVE SPRINT DAY 1 VERIFY ===\n")
    steps = [
        ("Compile", ["python3", "-m", "compileall", "-q", "app", "scripts", "tests"]),
        ("Unit tests (core)", ["python3", "-m", "unittest", "tests.test_observability", "tests.test_startup", "tests.test_health", "tests.test_go_live_day1", "-q"]),
        ("Route inventory", ["python3", "scripts/verify_route_inventory.py"]),
        ("Observability verify", ["python3", "scripts/verify_observability.py"]),
        ("Deployment verify", ["python3", "scripts/verify_deployment.py"]),
        ("API inventory generation", ["python3", "scripts/generate_api_inventory.py"]),
    ]

    for label, cmd in steps:
        if not run_command(label, cmd):
            sys.exit(1)

    if not verify_inventory_files():
        sys.exit(1)
    if not verify_health_endpoints():
        sys.exit(1)
    if not verify_startup_checks():
        sys.exit(1)

    print("\nGO-LIVE SPRINT DAY 1 VERIFY PASSED\n")


if __name__ == "__main__":
    main()
