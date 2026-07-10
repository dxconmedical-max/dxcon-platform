#!/usr/bin/env python3
"""Verify permission registry freeze — Release 2.0."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.architecture_freeze_lib import inventory_permissions, write_report


def main() -> int:
    report = inventory_permissions()
    report["status"] = "PASS" if report["registered_permission_count"] >= 10 else "FAIL"
    write_report("AUTHORIZATION_FREEZE_REPORT.json", report)
    print(f"Permission registry: {report['status']} count={report['registered_permission_count']}")
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
