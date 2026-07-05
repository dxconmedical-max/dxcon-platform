#!/usr/bin/env python3
"""Verify Operations Runbooks Phase 5 Sprint 5.11."""

from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = ROOT / "generated_release" / "OPERATIONS_RUNBOOKS_REPORT.json"
REPO = ROOT.parent

WEB_ROUTES = (
    "/operations-runbooks",
    "/operations-runbooks/go-live",
    "/operations-runbooks/backup",
    "/operations-runbooks/restore",
    "/operations-runbooks/rollback",
    "/operations-runbooks/incident",
)

API_ROUTES = (
    "/api/v1/operations-runbooks/dashboard",
    "/api/v1/operations-runbooks/go-live",
    "/api/v1/operations-runbooks/backup",
    "/api/v1/operations-runbooks/restore",
    "/api/v1/operations-runbooks/rollback",
    "/api/v1/operations-runbooks/incident",
    "/api/v1/operations-runbooks/inventory",
    "/api/v1/operations-runbooks/readiness",
)

RUNBOOK_FILES = (
    "GO_LIVE_RUNBOOK.md",
    "BACKUP_RUNBOOK.md",
    "RESTORE_RUNBOOK.md",
    "ROLLBACK_RUNBOOK.md",
    "INCIDENT_RUNBOOK.md",
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

    print("\n=== DXCON OPERATIONS RUNBOOKS VERIFY ===\n")
    start = time.perf_counter()
    checks: dict[str, dict] = {}

    from app import create_app

    app = create_app()
    with app.app_context():
        from app.core.passwords import hash_password
        from app.extensions.db import db
        from app.models.user import User

        db.create_all()
        if not User.query.filter(User.role.in_(("SUPER_ADMIN", "ADMIN"))).first():
            db.session.add(
                User(
                    email="verify-runbooks@demo.dxcon.test",
                    role="ADMIN",
                    password_hash=hash_password("DemoPass123!"),
                    is_active=True,
                )
            )
            db.session.commit()

        routes = {str(rule.rule) for rule in app.url_map.iter_rules()}
        missing_web = [route for route in WEB_ROUTES if route not in routes]
        missing_api = [route for route in API_ROUTES if route not in routes]
        checks["route_registry"] = {
            "ok": not missing_web and not missing_api,
            "missing_web": missing_web,
            "missing_api": missing_api,
        }

        missing_files = [name for name in RUNBOOK_FILES if not (REPO / "docs" / name).exists()]
        checks["runbook_files"] = {
            "ok": not missing_files,
            "missing": missing_files,
            "expected": list(RUNBOOK_FILES),
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
        checks["operations_runbooks_dashboard"] = {"ok": web_ok, "routes": web_results}

        api_ok = True
        api_results = {}
        for route in API_ROUTES:
            response = client.get(route, follow_redirects=True)
            ok = response.status_code == 200
            api_ok = api_ok and ok
            api_results[route] = {"status_code": response.status_code, "ok": ok}
        checks["api_endpoints"] = {"ok": api_ok, "routes": api_results}

        from app.services.operations_runbooks_service import FEATURES

        dashboard = _api_json(client.get("/api/v1/operations-runbooks/dashboard"))
        checks["feature_coverage"] = {
            "ok": len(dashboard.get("features", [])) == 5 and list(FEATURES) == dashboard.get("features"),
            "features": len(FEATURES),
        }

        for key, route in (
            ("go_live", "/api/v1/operations-runbooks/go-live"),
            ("backup", "/api/v1/operations-runbooks/backup"),
            ("restore", "/api/v1/operations-runbooks/restore"),
            ("rollback", "/api/v1/operations-runbooks/rollback"),
            ("incident", "/api/v1/operations-runbooks/incident"),
        ):
            payload = _api_json(client.get(route))
            checks[key] = {
                "ok": payload.get("exists") is True and len(payload.get("content", "")) > 100,
            }

        legacy_backup = client.get("/backup-recovery/runbook", follow_redirects=True)
        checks["legacy_backup_recovery_runbook_preserved"] = {"ok": legacy_backup.status_code == 200}

        legacy_release = client.get("/release-management/rollback", follow_redirects=True)
        checks["legacy_release_management_rollback_preserved"] = {"ok": legacy_release.status_code == 200}

    passed = sum(1 for item in checks.values() if item.get("ok"))
    total = len(checks)
    score = round((passed / total) * 100, 1) if total else 0.0
    report = {
        "generated_at": utc_now(),
        "phase": "5.11",
        "sprint": "Operations Runbooks",
        "summary": {
            "score": score,
            "checks_passed": passed,
            "checks_total": total,
            "ok": passed == total,
            "runtime_seconds": round(time.perf_counter() - start, 3),
        },
        "checks": checks,
        "readiness": _api_json(client.get("/api/v1/operations-runbooks/readiness"))
        if "client" in locals()
        else {},
    }
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")

    print(f"Operations Runbooks score: {score}%")
    print(f"Checks passed: {passed}/{total}")
    print(f"Report: {REPORT_PATH}")
    if report["summary"]["ok"]:
        print("OPERATIONS RUNBOOKS VERIFY PASS\n")
        return 0
    print("OPERATIONS RUNBOOKS VERIFY FAIL\n")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
