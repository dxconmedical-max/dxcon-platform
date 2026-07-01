#!/usr/bin/env python3
"""End-to-end go-live workflow validation for Release 4.8 RC1."""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from scripts.go_live_rc1_lib import run_full_rc1_validation


def main():
    print("\n=== DXCON E2E GO-LIVE VALIDATION ===\n")
    result = run_full_rc1_validation(write_reports=True)
    workflows = result["workflows"]
    for name, payload in workflows["workflows"].items():
        print(f"{'PASS' if payload.get('ok') else 'FAIL'}: {name}")

    print(
        f"\nWorkflows: {workflows['passed']}/{workflows['total']} | "
        f"Score: {result['score']['score']} | "
        f"RC1 ready: {result['score']['ready_for_rc1']}\n"
    )
    sys.exit(0 if result["ok"] else 1)


if __name__ == "__main__":
    main()
