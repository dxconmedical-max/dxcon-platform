#!/usr/bin/env python3
"""Final RC2 end-to-end smoke validation."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

from scripts.go_live_rc2_lib import run_rc2_validation


def main():
    print("\n=== DXCON FINAL RC2 SMOKE ===\n")
    result = run_rc2_validation(write_reports=True, run_regression=False)
    smoke = result["smoke"]
    for name, payload in smoke["steps"].items():
        print(f"{'PASS' if payload.get('ok') else 'FAIL'}: {name}")
    print(
        f"\nSmoke: {smoke['passed']}/{smoke['total']} | "
        f"RC2 score: {result['score']['score']} | "
        f"Ready: {result['score']['ready_for_rc2']}\n"
    )
    if not smoke["ok"]:
        sys.exit(1)
    print("FINAL RC2 SMOKE PASSED\n")


if __name__ == "__main__":
    main()
