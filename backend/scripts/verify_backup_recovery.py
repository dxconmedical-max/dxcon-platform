#!/usr/bin/env python3
"""Verify Backup & Disaster Recovery Phase 5 Sprint 5.3."""

from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = ROOT / "generated_release" / "BACKUP_RECOVERY_REPORT.json"

WEB_ROUTES = (
    "/backup-recovery",
    "/backup-recovery/scheduler",
    "/backup-recovery/restore",
    "/backup-recovery/pitr",
    "/backup-recovery/runbook",
)

API_ROUTES = (
    "/api/v1/backup-recovery/dashboard",
    "/api/v1/backup-recovery/scheduler",
    "/api/v1/backup-recovery/restore",
    "/api/v1/backup-recovery/pitr",
    "/api/v1/backup-recovery/runbook",
    "/api/v1/backup-recovery/inventory",
    "/api/v1/backup-recovery/readiness",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _login_admin(client):
    from app.models.user import User

    user = User.query.filter(User.role == "SUPER_ADMIN").first()
    if not user:
        user = User.query.filter(User.role == "ADMIN").first()
    if not user:
        return False
    with client.session_transaction() as sess:
        sess["user_id"] = user.id
        sess["role"] = user.role
        sess["email"] = user.email
    return True


def _api_json(response):
    payload = response.get_json() or {}
    if isinstance(payload, dict) and payload.get("success") is True and "data" in payload:
        return payload["data"]
    return payload


def main() -> int:
    sys.path.insert(0, str(ROOT))
    if not os.getenv("DATABASE_URL"):
        print("FAIL: DATABASE_URL is required", file=sys.stderr)
        return 1

    print("\n=== DXCON BACKUP & DISASTER RECOVERY VERIFY ===\n")
    start = time.perf_counter()
    checks: dict[str, dict] = {}

    from app import create_app

    app = create_app()
    with app.app_context():
        from app.core.passwords import hash_password
        from app.extensions.db import db
        from app.models.user import User
        from app.operations.backup_service import BackupService
        from app.operations.scheduler_service import SchedulerService

        db.create_all()
        if not User.query.filter(User.role.in_(("SUPER_ADMIN", "ADMIN"))).first():
            db.session.add(
                User(
                    email="verify-backup@demo.dxcon.test",
                    role="ADMIN",
                    password_hash=hash_password("DemoPass123!"),
                    is_active=True,
                )
            )
            db.session.commit()

        SchedulerService.ensure_defaults()
        BackupService.run_backup({"backup_type": "DATABASE"})
        BackupService.validate_backup(
            BackupService.list_backups()["backups"][0]["id"]
        )

        routes = {str(rule.rule) for rule in app.url_map.iter_rules()}
        missing_web = [route for route in WEB_ROUTES if route not in routes]
        missing_api = [route for route in API_ROUTES if route not in routes]
        checks["route_registry"] = {
            "ok": not missing_web and not missing_api,
            "missing_web": missing_web,
            "missing_api": missing_api,
        }

        client = app.test_client()
        if not _login_admin(client):
            checks["auth"] = {"ok": False, "reason": "no admin user"}
        else:
            checks["auth"] = {"ok": True}

        web_ok = True
        web_results = {}
        for route in WEB_ROUTES:
            response = client.get(route, follow_redirects=True)
            ok = response.status_code == 200 and len(response.get_data(as_text=True)) > 200
            web_ok = web_ok and ok
            web_results[route] = {"status_code": response.status_code, "ok": ok}
        checks["backup_dashboard"] = {"ok": web_ok, "routes": web_results}

        api_ok = True
        api_results = {}
        for route in API_ROUTES:
            response = client.get(route, follow_redirects=True)
            ok = response.status_code == 200
            api_ok = api_ok and ok
            api_results[route] = {"status_code": response.status_code, "ok": ok}
        checks["api_endpoints"] = {"ok": api_ok, "routes": api_results}

        from app.services.backup_recovery_service import FEATURES, dashboard_payload, backup_readiness_report

        dashboard = dashboard_payload()
        readiness = backup_readiness_report()
        checks["feature_coverage"] = {
            "ok": len(dashboard.get("features", [])) == 5 and list(FEATURES) == dashboard.get("features"),
            "features": len(FEATURES),
        }

        checks["backup_scheduler"] = {
            "ok": "default_jobs" in _api_json(client.get("/api/v1/backup-recovery/scheduler")),
        }
        checks["restore_verification"] = {
            "ok": _api_json(client.get("/api/v1/backup-recovery/restore")).get("read_only") is True,
        }
        checks["pitr_checklist"] = {
            "ok": len(_api_json(client.get("/api/v1/backup-recovery/pitr")).get("items", [])) >= 5,
        }
        checks["disaster_recovery_runbook"] = {
            "ok": "scenarios" in _api_json(client.get("/api/v1/backup-recovery/runbook")),
        }
        checks["backup_inventory"] = {
            "ok": _api_json(client.get("/api/v1/backup-recovery/inventory")).get("backups_total", 0) >= 1,
        }

        backup_id = BackupService.list_backups()["backups"][0]["id"]
        dry_run = _api_json(
            client.post("/api/v1/backup-recovery/restore/dry-run", json={"backup_id": backup_id})
        )
        checks["restore_dry_run"] = {"ok": dry_run.get("validation", {}).get("status") == "PASSED"}

        legacy = client.get("/operations/backups")
        checks["legacy_operations_backups_preserved"] = {"ok": legacy.status_code == 200}

        existing_payload = _api_json(client.get("/api/v1/operations/backups"))
        checks["existing_operations_api_preserved"] = {
            "ok": existing_payload.get("count", 0) >= 1,
        }

    passed = sum(1 for item in checks.values() if item.get("ok"))
    total = len(checks)
    score = round((passed / total) * 100, 1) if total else 0.0
    report = {
        "generated_at": utc_now(),
        "phase": "5.3",
        "sprint": "Backup & Disaster Recovery",
        "summary": {
            "score": score,
            "checks_passed": passed,
            "checks_total": total,
            "ok": passed == total,
            "runtime_seconds": round(time.perf_counter() - start, 3),
        },
        "checks": checks,
        "readiness": readiness if "readiness" in locals() else {},
    }
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")

    print(f"Backup & Disaster Recovery score: {score}%")
    print(f"Checks passed: {passed}/{total}")
    print(f"Report: {REPORT_PATH}")
    if report["summary"]["ok"]:
        print("BACKUP & DISASTER RECOVERY VERIFY PASS\n")
        return 0
    print("BACKUP & DISASTER RECOVERY VERIFY FAIL\n")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
