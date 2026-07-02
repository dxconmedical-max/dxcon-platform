#!/usr/bin/env python3
"""Verify enterprise hardening pack 2 standards."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from enterprise_hardening_lib import run_enterprise_hardening_verification


def main() -> int:
    result = run_enterprise_hardening_verification()
    print("\n=== DXCON ENTERPRISE HARDENING PACK 2 ===\n")
    for section_name, section in result.get("sections", {}).items():
        print(f"{'PASS' if section.get('ok') else 'FAIL'}: {section_name}")
        checks = section.get("checks")
        if isinstance(checks, dict):
            for name, payload in checks.items():
                if isinstance(payload, dict) and "ok" in payload:
                    print(f"  {'PASS' if payload.get('ok') else 'FAIL'}: {name}")
    if result.get("ok"):
        print("\nENTERPRISE HARDENING PACK 2 PASSED\n")
        return 0
    print("\nENTERPRISE HARDENING PACK 2 FAILED\n")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
