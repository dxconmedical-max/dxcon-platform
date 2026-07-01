#!/usr/bin/env python3
"""Final security and secrets preflight review."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.security_preflight_lib import run_security_preflight


def main():
    print("\n=== DXCON SECURITY PREFLIGHT ===\n")
    result = run_security_preflight()
    for name, payload in result["checks"].items():
        print(f"{'PASS' if payload.get('ok') else 'FAIL'}: {name}")
    print(f"\nSUMMARY: {result['passed']}/{result['total']} passed")
    if not result["ok"]:
        sys.exit(1)
    print("SECURITY PREFLIGHT PASSED\n")


if __name__ == "__main__":
    main()
