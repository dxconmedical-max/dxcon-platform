#!/usr/bin/env python3
"""Verify admin route protection for staging security review."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.security_preflight_lib import run_security_preflight


def main():
    print("\n=== DXCON ADMIN SECURITY VERIFY ===\n")
    result = run_security_preflight()
    admin = result["checks"]["admin_protection"]
    print(f"Protected admin routes: {len(admin['protected'])}")
    print(f"Allowlisted internal routes: {len(admin['allowlisted'])}")
    if admin["unprotected"]:
        print("UNPROTECTED:")
        for path in admin["unprotected"]:
            print(f"  - {path}")
    for item in admin["allowlisted"]:
        print(f"  INTERNAL {item['path']} ({item['note']})")
    if not admin["ok"]:
        sys.exit(1)
    print("\nADMIN SECURITY VERIFY PASSED\n")


if __name__ == "__main__":
    main()
