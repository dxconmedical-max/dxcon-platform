#!/usr/bin/env python3
"""Verify API v1 contract freeze — Release 2.0."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.architecture_freeze_lib import create_app, inventory_api_routes, write_report


def main() -> int:
    app = create_app()
    report = inventory_api_routes(app)
    report["status"] = "PASS" if report["duplicate_count"] == 0 and report["stable_count"] > 0 else "FAIL"
    write_report("API_V1_FREEZE_REPORT.json", report)
    print(f"API v1 freeze: {report['status']} stable={report['stable_count']} dup={report['duplicate_count']}")
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
