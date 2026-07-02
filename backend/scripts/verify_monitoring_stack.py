#!/usr/bin/env python3
"""Verify observability and monitoring stack readiness."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.monitoring_stack_lib import run_monitoring_stack_verification


def main():
    print("\n=== DXCON MONITORING STACK VERIFY ===\n")
    result = run_monitoring_stack_verification()
    for name, payload in result["checks"].items():
        print(f"{'PASS' if payload.get('ok') else 'FAIL'}: {name}")
        if name == "alert_rules" and payload.get("missing"):
            print("  missing alerts:", payload["missing"])
        if name == "prometheus_metrics" and payload.get("missing"):
            print("  missing metrics:", payload["missing"])
        if name == "grafana" and payload.get("missing_panels"):
            print("  missing panels:", payload["missing_panels"])
    print(f"\nSUMMARY: {result['passed']}/{result['total']} passed")
    if not result["ok"]:
        sys.exit(1)
    print("MONITORING STACK VERIFY PASSED\n")


if __name__ == "__main__":
    main()
