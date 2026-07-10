#!/usr/bin/env python3
"""Verify mobile API completion — Epic 7."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "generated_release"


def main() -> int:
    sys.path.insert(0, str(ROOT))
    from app import create_app

    app = create_app()
    client = app.test_client()
    routes = {r.rule for r in app.url_map.iter_rules()}
    required = [
        "/api/v1/mobile/app-config",
        "/api/v1/mobile/devices",
        "/api/v1/mobile/patient/dashboard",
        "/api/v1/mobile/patient/bookings",
        "/api/v1/mobile/patient/results",
        "/api/v1/mobile/collector/jobs",
        "/api/v1/mobile/audit/events",
    ]
    missing = [r for r in required if r not in routes]
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "PASS" if not missing else "FAIL",
        "required": required,
        "missing": missing,
    }
    GENERATED.mkdir(parents=True, exist_ok=True)
    (GENERATED / "MOBILE_API_COMPLETION_REPORT.json").write_text(json.dumps(report, indent=2))
    print(f"Mobile API completion: {report['status']}")
    return 0 if not missing else 1


if __name__ == "__main__":
    raise SystemExit(main())
