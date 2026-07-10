#!/usr/bin/env python3
"""Verify clinical state machine freeze — Release 2.0."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.architecture_freeze_lib import inventory_state_machines, write_report


def main() -> int:
    report = inventory_state_machines()
    ok = bool(report["transition_maps"]) and report["order_state_coverage"] >= 5
    report["status"] = "PASS" if ok else "FAIL"
    write_report("CLINICAL_WORKFLOW_FREEZE_REPORT.json", report)
    print(f"Clinical workflows: {report['status']} maps={list(report['transition_maps'])}")
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
