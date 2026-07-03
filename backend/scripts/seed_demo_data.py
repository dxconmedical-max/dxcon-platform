#!/usr/bin/env python3
"""Seed idempotent demo dataset for staging/production demos."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app import create_app
from app.extensions.db import db
from scripts.demo_seed_lib import REPORT_PATH, run_seed


def main() -> int:
    parser = argparse.ArgumentParser(description="Seed DxCon demo dataset")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--dry-run", action="store_true", help="Plan seed actions without writing")
    group.add_argument("--apply", action="store_true", help="Apply demo seed data")
    group.add_argument("--summary", action="store_true", help="Summarize existing demo rows")
    args = parser.parse_args()

    if not os.getenv("DATABASE_URL"):
        print("FAIL: DATABASE_URL is required", file=sys.stderr)
        return 1

    print("\n=== DXCON DEMO DATA SEED ===\n")
    app = create_app()
    with app.app_context():
        db.create_all()
        if args.summary:
            report = run_seed(summary_only=True)
        elif args.dry_run:
            report = run_seed(dry_run=True)
        else:
            report = run_seed(dry_run=False)

    print(f"Mode: {report['mode']}")
    print(f"Runtime: {report['runtime_seconds']}s")
    print(f"Report: {REPORT_PATH}\n")
    for name, count in sorted(report.get("created_counts", {}).items()):
        existing = report.get("existing_counts", {}).get(name, 0)
        print(f"{name}: created={count} existing={existing}")
    if report.get("skipped_models"):
        print("\nSkipped optional domains:")
        for item in report["skipped_models"]:
            print(f"  - {item['model']}: {item['reason']}")
    if report.get("errors"):
        print("\nErrors:")
        for error in report["errors"]:
            print(f"  - {error}")
        return 1
    print("\nDEMO SEED COMPLETE\n" if args.apply else "\nDEMO SEED DRY-RUN COMPLETE\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
