#!/usr/bin/env python3
"""Verify integration platform hardening stack."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from integration_hardening_lib import run_integration_hardening_verification


def main() -> int:
    result = run_integration_hardening_verification()
    checks = result.get("checks", {})
    print("\n=== DXCON INTEGRATION HARDENING VERIFY ===\n")
    for name, payload in checks.items():
        status = "PASS" if payload.get("ok") else "FAIL"
        print(f"{status}: {name}")
        if not payload.get("ok"):
            for key, value in payload.items():
                if key != "ok":
                    print(f"  {key}: {value}")
    print(f"\nSUMMARY: {result.get('passed')}/{result.get('total')} passed")
    if result.get("ok"):
        print("INTEGRATION HARDENING VERIFY PASSED\n")
        return 0
    print("INTEGRATION HARDENING VERIFY FAILED\n")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
