#!/usr/bin/env python3
"""Verify staging deployment stack readiness."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.staging_stack_lib import run_staging_verification


def main():
    print("\n=== DXCON STAGING STACK VERIFY ===\n")
    result = run_staging_verification()
    for name, payload in result["checks"].items():
        print(f"{'PASS' if payload.get('ok') else 'FAIL'}: {name}")
    print(f"\nSUMMARY: {result['passed']}/{result['total']} passed")
    if not result["ok"]:
        sys.exit(1)
    print("STAGING STACK VERIFY PASSED\n")


if __name__ == "__main__":
    main()
