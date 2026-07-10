#!/usr/bin/env python3
"""Epic 8 — Production readiness verification."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

from production_readiness_lib import utc_now, write_report  # noqa: E402


def main() -> int:
    from app import create_app
    from app.extensions.db import db
    from app.pilot_readiness.audit import run_production_readiness_audit

    app = create_app()
    with app.app_context():
        db.create_all()
        audit = run_production_readiness_audit(app)

    score = audit["production_readiness_score"]
    status = audit["grade"]
    report = {
        "generated_at": utc_now(),
        "status": status,
        "production_readiness_score": score,
        "summary": audit["summary"],
        "findings_count": len(audit["findings"]),
        "critical_blockers": audit["summary"].get("critical_blockers", []),
    }
    path = write_report("PRODUCTION_READINESS_SCORE.json", report)
    print(f"\n=== DXCON PRODUCTION VERIFY ===\n")
    print(f"Score: {score}/100 ({status})")
    print(f"Report: {path}")
    if report["critical_blockers"]:
        print("Blockers:", report["critical_blockers"])
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
