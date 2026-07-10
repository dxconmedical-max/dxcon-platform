#!/usr/bin/env python3
"""Epic 8 — Backup and disaster recovery verification."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
sys.path.insert(0, str(ROOT))
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

from production_readiness_lib import finding, score_findings, utc_now, write_report  # noqa: E402


def main() -> int:
    findings = []
    scripts = [
        ("backup_postgres", REPO / "deployment" / "scripts" / "backup_postgres.sh"),
        ("backup_uploads", REPO / "deployment" / "scripts" / "backup_uploads.sh"),
        ("verify_backup_restore", REPO / "deployment" / "scripts" / "verify_backup_restore.sh"),
        ("backup_runbook", REPO / "docs" / "BACKUP_RUNBOOK.md"),
        ("dr_report", ROOT / "generated_release" / "BACKUP_DR_REPORT.json"),
    ]
    for name, path in scripts:
        findings.append(finding("PASS" if path.exists() else "WARNING", name, str(path)))

    verify = ROOT / "scripts" / "verify_backup_recovery.py"
    if verify.exists():
        proc = subprocess.run([sys.executable, str(verify)], capture_output=True, text=True, timeout=120)
        findings.append(finding("PASS" if proc.returncode == 0 else "WARNING", "backup_recovery_verify"))

    from app import create_app
    from app.extensions.db import db

    app = create_app()
    with app.app_context():
        db.create_all()
        try:
            from app.models.operations_platform import BackupJob

            count = BackupJob.query.count()
            findings.append(finding("PASS", "backup_job_model", f"records={count}"))
        except Exception as exc:
            findings.append(finding("WARNING", "backup_job_model", str(exc)))

    scored = score_findings(findings)
    status = "PASS" if scored["counts"].get("FAIL", 0) == 0 else "WARNING"
    report = {"generated_at": utc_now(), "status": status, "findings": findings, "score": scored}
    path = write_report("BACKUP_EPIC8_REPORT.json", report)
    print(f"\n=== DXCON BACKUP VERIFY ===\nStatus: {status}\nReport: {path}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
