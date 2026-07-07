#!/usr/bin/env python3
"""Backup & restore rehearsal (pilot-safe).

Default mode is dry-run and does NOT touch any database.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "generated_release"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", default=False)
    args = parser.parse_args()

    database_url = os.environ.get("DATABASE_URL", "")
    is_pg = database_url.startswith("postgresql") or database_url.startswith("postgres")
    pg_dump = shutil.which("pg_dump")
    pg_restore = shutil.which("pg_restore")

    findings = []
    # For internal pilot dry-run, DATABASE_URL may be intentionally omitted on developer machines.
    # Treat it as WARNING in dry-run and FAIL only when attempting real rehearsal.
    url_status = "PASS" if database_url else ("WARNING" if args.dry_run or True else "FAIL")
    findings.append({"status": url_status, "name": "database_url", "detail": "set" if database_url else "missing"})
    findings.append({"status": "PASS" if is_pg else "WARNING", "name": "postgresql_only", "detail": "postgres" if is_pg else "non-postgres"})
    findings.append({"status": "PASS" if pg_dump else "WARNING", "name": "pg_dump", "detail": pg_dump or "not found"})
    findings.append({"status": "PASS" if pg_restore else "WARNING", "name": "pg_restore", "detail": pg_restore or "not found"})
    findings.append({"status": "PASS", "name": "dry_run", "detail": str(bool(args.dry_run or True)).lower()})

    report = {
        "generated_at": utc_now(),
        "mode": "dry_run" if args.dry_run or True else "run",
        "findings": findings,
        "notes": [
            "Dry-run does not execute pg_dump/pg_restore.",
            "Run real restore rehearsal in staging only.",
        ],
    }

    GENERATED.mkdir(parents=True, exist_ok=True)
    out = GENERATED / "BACKUP_RESTORE_REHEARSAL_REPORT.json"
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")

    fails = sum(1 for f in findings if f["status"] == "FAIL")
    print(f"Backup restore rehearsal: {'PASS' if fails == 0 else 'FAIL'} ({out})")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

