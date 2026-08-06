#!/usr/bin/env python3
"""Apply SampleCollection / full ORM schema reconciliation (PostgreSQL).

Canonical migration:
  backend/migrations/021_schema_reconciliation.sql

This runner delegates to apply_migrations.py so DO $$ blocks and the full
ORM sync are applied correctly (not one column at a time).

Usage:
  cd backend
  python scripts/apply_sample_collections_collection_mode.py
  python scripts/apply_sample_collections_collection_mode.py --verify-only
  python scripts/apply_sample_collections_collection_mode.py --json
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

MIGRATION_NAME = "021_schema_reconciliation.sql"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify-only", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    # Delegate to the production migration runner (reconciliation only).
    from apply_migrations import main as apply_main

    argv = ["apply_migrations.py", "--only", MIGRATION_NAME]
    if args.verify_only:
        argv.append("--verify-only")
    if args.json:
        argv.append("--json")
    sys.argv = argv
    return apply_main()


if __name__ == "__main__":
    raise SystemExit(main())
