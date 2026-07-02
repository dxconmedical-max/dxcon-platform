#!/usr/bin/env python3
"""Verify Enterprise Hardening Pack 3 - Database Excellence."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.database_excellence_lib import run_database_excellence_verification
from scripts.enterprise_master_lib import print_verify_banner


def main() -> int:
    result = run_database_excellence_verification()
    print_verify_banner("DXCON ENTERPRISE PACK 3 - DATABASE EXCELLENCE", result.get("sections", {}))
    if result.get("ok"):
        print("\nENTERPRISE PACK 3 PASSED\n")
        return 0
    print("\nENTERPRISE PACK 3 FAILED\n")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
