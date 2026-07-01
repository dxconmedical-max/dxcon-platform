#!/usr/bin/env python3
"""Final GA smoke — consolidated UAT, RC2, security, and staging checks."""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

from scripts.ga_candidate_lib import run_ga_smoke_suite


def main():
    print("\n=== DXCON FINAL GA SMOKE ===\n")
    result = run_ga_smoke_suite()
    for name, payload in result["suites"].items():
        detail = ""
        if "passed" in payload and "total" in payload:
            detail = f" ({payload['passed']}/{payload['total']})"
        print(f"{'PASS' if payload.get('ok') else 'FAIL'}: {name}{detail}")
    print(f"\nSmoke suites: {result['passed']}/{result['total']}")
    if not result["ok"]:
        sys.exit(1)
    print("FINAL GA SMOKE PASSED\n")


if __name__ == "__main__":
    main()
