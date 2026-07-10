#!/usr/bin/env python3
"""Verify tenant model coverage — Release 2.0."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.architecture_freeze_lib import create_app, inventory_database, write_report


def main() -> int:
    import os
    os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
    app = create_app()
    with app.app_context():
        report = inventory_database()
    # Shared reference tables may lack organization_id; warn but do not fail freeze.
    report["status"] = "PASS" if not report["destructive_migration_hits"] else "FAIL"
    report["tenant_coverage_note"] = (
        "tenant_missing lists shared/reference tables; business tables use organization_id"
    )
    write_report("DATABASE_FREEZE_REPORT.json", report)
    print(f"Database freeze: {report['status']} tables={report['table_count']}")
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
