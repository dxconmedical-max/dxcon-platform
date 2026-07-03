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
from app.infrastructure.production_readiness import app_env, is_strict_env
from scripts.demo_seed_lib import REPORT_PATH, run_seed


def apply_create_all_guard(app, allow_create_all: bool) -> dict:
    env = app_env(app)
    if is_strict_env(app):
        return {
            "executed": False,
            "app_env": env,
            "reason": f"forbidden_in_{env}",
        }
    if allow_create_all:
        db.create_all()
        return {
            "executed": True,
            "app_env": env,
            "reason": "--allow-create-all",
        }
    return {
        "executed": False,
        "app_env": env,
        "reason": "development_requires_--allow-create-all",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Seed DxCon demo dataset")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--dry-run", action="store_true", help="Plan seed actions without writing")
    group.add_argument("--apply", action="store_true", help="Apply demo seed data")
    group.add_argument("--summary", action="store_true", help="Summarize existing demo rows")
    parser.add_argument(
        "--allow-create-all",
        action="store_true",
        help="Allow db.create_all() in development/local only (never production/staging)",
    )
    args = parser.parse_args()

    if not os.getenv("DATABASE_URL"):
        print("FAIL: DATABASE_URL is required", file=sys.stderr)
        return 1

    print("\n=== DXCON DEMO DATA SEED ===\n")
    app = create_app()
    with app.app_context():
        create_all_meta = apply_create_all_guard(app, args.allow_create_all)
        if args.summary:
            report = run_seed(summary_only=True, create_all_meta=create_all_meta)
        elif args.dry_run:
            report = run_seed(dry_run=True, create_all_meta=create_all_meta)
        else:
            report = run_seed(dry_run=False, create_all_meta=create_all_meta)

    print(f"Mode: {report['mode']}")
    print(f"Runtime: {report['runtime_seconds']}s")
    print(f"Report: {REPORT_PATH}\n")
    create_all = report.get("create_all", {})
    print(
        "create_all: "
        f"executed={create_all.get('executed', False)} "
        f"reason={create_all.get('reason', 'unknown')}"
    )
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
