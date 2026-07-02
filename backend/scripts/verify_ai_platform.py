#!/usr/bin/env python3
"""Verify AI platform foundation stack."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ai_platform_lib import run_ai_platform_verification


def main() -> int:
    result = run_ai_platform_verification()
    checks = result.get("checks", {})
    print("\n=== DXCON AI PLATFORM VERIFY ===\n")
    for name, payload in checks.items():
        status = "PASS" if payload.get("ok") else "FAIL"
        print(f"{status}: {name}")
        if not payload.get("ok"):
            for key, value in payload.items():
                if key != "ok":
                    print(f"  {key}: {value}")
    print(f"\nSUMMARY: {result.get('passed')}/{result.get('total')} passed")
    if result.get("ok"):
        print("AI PLATFORM VERIFY PASSED\n")
        return 0
    print("AI PLATFORM VERIFY FAILED\n")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
