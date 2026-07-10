#!/usr/bin/env python3
"""Verify domain event contract freeze — Release 2.0."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.architecture_freeze_lib import inventory_domain_events, write_report


def main() -> int:
    report = inventory_domain_events()
    report["status"] = "PASS" if len(report["implemented_legacy_events"]) >= 5 else "FAIL"
    write_report("DOMAIN_EVENT_FREEZE_REPORT.json", report)
    print(f"Domain events: {report['status']} implemented={len(report['implemented_legacy_events'])}")
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
