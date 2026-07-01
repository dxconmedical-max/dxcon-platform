#!/usr/bin/env python3
"""Verify staging monitoring, backup, and restore readiness."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.staging_monitoring_lib import run_monitoring_verification


def main():
    print("\n=== DXCON STAGING MONITORING VERIFY ===\n")
    result = run_monitoring_verification()
    for name, payload in result["checks"].items():
        print(f"{'PASS' if payload.get('ok') else 'FAIL'}: {name}")
    print(f"\nSUMMARY: {result['passed']}/{result['total']} passed")
    if not result["ok"]:
        sys.exit(1)
    print("STAGING MONITORING VERIFY PASSED\n")


if __name__ == "__main__":
    main()
