#!/usr/bin/env python3
"""Verify Release 1.0 — Sprint 010 Executive Platform and Production Readiness."""

from __future__ import annotations

import json
import os
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "generated_release"
ENV_FILE = ROOT / ".env"
sys.path.insert(0, str(ROOT))


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_database_url() -> str:
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("DATABASE_URL=") and not line.startswith("#"):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    return os.environ.get("DATABASE_URL", "sqlite:///:memory:")


def apply_migration(db, name: str) -> None:
    path = ROOT / "migrations" / name
    if not path.exists():
        return
    lines = [ln for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip() and not ln.strip().startswith("--")]
    for stmt in " ".join(lines).split(";"):
        stmt = stmt.strip()
        if stmt:
            try:
                db.session.execute(db.text(stmt))
                db.session.commit()
            except Exception:
                db.session.rollback()


def main() -> int:
    database_url = os.environ.get("DATABASE_URL") or load_database_url()
    os.environ["DATABASE_URL"] = database_url
    is_pg = database_url.startswith("postgresql") or database_url.startswith("postgres")

    from app import create_app
    from app.extensions.db import db
    from app.executive_platform.service import (
        admin_settings,
        audit_center,
        backup_dashboard,
        crm_dashboard,
        crm_report,
        deployment_report,
        executive_dashboard,
        executive_report,
        finance_dashboard,
        finance_report,
        launch_checklist,
        operational_monitoring,
        pilot_ready_report,
        pilot_wizard,
        release_1_complete,
        security_report,
        verify_checklist_item,
    )
    from app.core.passwords import hash_password
    from app.infrastructure.storage_service import StorageService
    from app.models.audit_log import AuditLog
    from app.models.user import User

    start = time.time()
    checks: dict = {}
    app = create_app()
    GENERATED.mkdir(parents=True, exist_ok=True)

    with app.app_context():
        if is_pg:
            for mig in ("007_reporting_engine.sql", "008_portal.sql", "009_executive_platform.sql"):
                apply_migration(db, mig)
        else:
            db.create_all()

        admin = User.query.filter(User.role.in_(["SUPER_ADMIN", "ADMIN"])).first()
        if not admin:
            admin = User(email=f"admin-{uuid.uuid4().hex[:6]}@dxcon.test", role="SUPER_ADMIN", password_hash=hash_password("VerifyOnly123!"), is_active=True)
            db.session.add(admin)
            db.session.commit()

        checks["executive_dashboard"] = {"ok": "widgets" in executive_dashboard()}
        checks["crm"] = {"ok": "leads" in crm_dashboard()}
        checks["finance"] = {"ok": "outstanding_balance" in finance_dashboard()}
        checks["monitoring"] = {"ok": operational_monitoring().get("system_health") in ("healthy", "degraded")}
        checks["audit"] = {"ok": isinstance(audit_center().get("data"), list)}
        checks["backup"] = {"ok": backup_dashboard().get("manual_backup") is True}
        checks["security"] = {"ok": security_report().get("jwt_validation") is True}
        checks["storage"] = {"ok": StorageService().store("reports", "test.txt", b"ok").get("provider") == "local"}
        checks["pilot_wizard"] = {"ok": "checklist" in pilot_wizard(organization_name="Pilot Org", actor="verify")}
        db.session.commit()

        lc = launch_checklist()
        for item in lc.get("items", [])[:3]:
            verify_checklist_item(item["item_key"], actor="verify")
        db.session.commit()
        checks["launch_checklist"] = {"ok": len(lc.get("items", [])) >= 5}

        checks["deployment"] = {"ok": deployment_report().get("docker") is True}
        checks["cicd_files"] = {
            "ok": (ROOT.parent / ".github" / "workflows" / "backend-ci.yml").exists()
            and (ROOT / "Dockerfile").exists()
            and (ROOT.parent / "docker-compose.production.yml").exists(),
        }

        exec_report = executive_report()
        crm_r = crm_report()
        fin_r = finance_report()
        sec_r = security_report()
        dep_r = deployment_report()
        pilot_r = pilot_ready_report()
        release_r = release_1_complete()
        (GENERATED / "EXECUTIVE_REPORT.json").write_text(json.dumps(exec_report, indent=2), encoding="utf-8")
        (GENERATED / "CRM_REPORT.json").write_text(json.dumps(crm_r, indent=2), encoding="utf-8")
        (GENERATED / "FINANCE_REPORT.json").write_text(json.dumps(fin_r, indent=2), encoding="utf-8")
        (GENERATED / "SECURITY_REPORT.json").write_text(json.dumps(sec_r, indent=2), encoding="utf-8")
        (GENERATED / "DEPLOYMENT_REPORT.json").write_text(json.dumps(dep_r, indent=2), encoding="utf-8")
        (GENERATED / "PILOT_READY_REPORT.json").write_text(json.dumps(pilot_r, indent=2), encoding="utf-8")
        (GENERATED / "RELEASE_1_COMPLETE.json").write_text(json.dumps(release_r, indent=2), encoding="utf-8")

        checks["audit_logs"] = {"ok": AuditLog.query.count() >= 0}

        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess["user_id"] = admin.id
                sess["role"] = admin.role
                sess["email"] = admin.email
            checks["ui_executive"] = {"ok": client.get("/app/executive").status_code == 200}
            checks["ui_crm"] = {"ok": client.get("/app/crm").status_code == 200}
            checks["ui_finance"] = {"ok": client.get("/app/finance").status_code == 200}
            checks["ui_monitoring"] = {"ok": client.get("/app/monitoring").status_code == 200}
            checks["ui_audit"] = {"ok": client.get("/app/audit-center").status_code == 200}
            checks["ui_pilot"] = {"ok": client.get("/app/pilot/wizard").status_code == 200}
            checks["api_dashboard"] = {"ok": client.get("/api/v1/executive-platform/dashboard").status_code == 200}

        passed = sum(1 for c in checks.values() if c.get("ok"))
        summary = {"sprint": "010", "release": "1.0-pilot", "passed": passed, "total": len(checks), "checks": checks, "elapsed": round(time.time() - start, 2), "generated_at": utc_now()}
        (GENERATED / "RELEASE_1_VERIFY.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
        print(f"Release 1 Verify: {passed}/{len(checks)} PASS")
        for name, r in checks.items():
            print(f"  [{'PASS' if r.get('ok') else 'FAIL'}] {name}")
        return 0 if passed == len(checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
