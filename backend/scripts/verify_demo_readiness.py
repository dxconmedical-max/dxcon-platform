#!/usr/bin/env python3
"""Verify demo readiness artifacts and routes."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
REPORT_PATH = ROOT / "generated_release" / "DEMO_READINESS_REPORT.json"

REQUIRED_FILES = (
    "scripts/seed_demo_data.py",
    "scripts/demo_seed_lib.py",
    "scripts/smoke_production_api.py",
    "docs/DEMO_SEED_DATA.md",
    "docs/DEMO_SEED_RUNBOOK.md",
    "docs/PRODUCTION_SMOKE_TEST.md",
)

REQUIRED_ROUTES = (
    "/",
    "/health",
    "/ready",
    "/live",
    "/executive-v9",
    "/crm-pipeline",
    "/logistics",
    "/collector",
    "/doctor/dashboard",
    "/api/v1/workflow/health",
    "/api/v1/openapi.json",
    "/api-docs",
)


def main() -> int:
    sys.path.insert(0, str(ROOT))
    print("\n=== DXCON DEMO READINESS VERIFY ===\n")
    checks = {}

    try:
        from app import create_app  # noqa: WPS433

        checks["app_imports"] = {"ok": True}
    except Exception as exc:
        checks["app_imports"] = {"ok": False, "error": str(exc)}

    missing_files = [path for path in REQUIRED_FILES if not (ROOT / path).exists()]
    checks["required_files"] = {"ok": not missing_files, "missing": missing_files}

    generated_dir = ROOT / "generated_release"
    checks["generated_release_directory"] = {
        "ok": generated_dir.exists() and generated_dir.is_dir(),
        "path": str(generated_dir),
    }

    route_check = {"ok": False, "missing": [], "count": 0}
    if checks["app_imports"]["ok"]:
        import os

        os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
        from app import create_app

        app = create_app()
        routes = {str(rule.rule) for rule in app.url_map.iter_rules()}
        missing_routes = [route for route in REQUIRED_ROUTES if route not in routes]
        route_check = {
            "ok": not missing_routes,
            "missing": missing_routes,
            "count": len(routes),
        }
    checks["required_routes"] = route_check

    passed = sum(1 for item in checks.values() if item.get("ok"))
    report = {
        "checks": checks,
        "summary": {
            "passed": passed,
            "total": len(checks),
            "ok": passed == len(checks),
        },
    }
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")

    for name, payload in checks.items():
        print(f"{'PASS' if payload.get('ok') else 'FAIL'}: {name}")
        if not payload.get("ok"):
            for key, value in payload.items():
                if key != "ok" and value:
                    print(f"  {key}: {value}")
    print(f"\nSummary: {passed}/{len(checks)} passed")
    print(f"Report: {REPORT_PATH}\n")
    return 0 if report["summary"]["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
