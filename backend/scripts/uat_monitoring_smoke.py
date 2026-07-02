#!/usr/bin/env python3
"""UAT monitoring smoke — metrics, logs, alerts, and dashboard readiness."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.monitoring_stack_lib import run_uat_monitoring_smoke


def main():
    print("\n=== DXCON UAT MONITORING SMOKE ===\n")
    result = run_uat_monitoring_smoke()
    for name, ok in result["steps"].items():
        print(f"{'PASS' if ok else 'FAIL'}: {name}")
    print(f"\nUAT monitoring: {result['passed']}/{result['total']}")
    if not result["ok"]:
        sys.exit(1)
    print("UAT MONITORING SMOKE PASSED\n")


if __name__ == "__main__":
    main()
