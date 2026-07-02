#!/usr/bin/env python3
"""Verify environment file safety and example coverage."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from env_safety_lib import run_env_safety_verification


def main() -> int:
    result = run_env_safety_verification()
    print("\n=== DXCON ENV SAFETY VERIFY ===\n")
    for name, payload in result.get("checks", {}).items():
        print(f"{'PASS' if payload.get('ok') else 'FAIL'}: {name}")
        if not payload.get("ok"):
            for key, value in payload.items():
                if key != "ok":
                    print(f"  {key}: {value}")
    print(f"\nSUMMARY: {result.get('passed')}/{result.get('total')} passed")
    if result.get("ok"):
        print("ENV SAFETY VERIFY PASSED\n")
        return 0
    print("ENV SAFETY VERIFY FAILED\n")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
