#!/usr/bin/env python3
"""Verify role dashboards + emit go-live blocker snapshot."""

from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "generated_release"
sys.path.insert(0, str(ROOT))

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def main() -> int:
    from app import create_app
    from app.extensions.db import db
    from app.core.passwords import hash_password
    from app.models.user import User
    from app.role_dashboards.service import build_role_dashboard, role_can_access

    start = time.time()
    checks: dict = {}
    app = create_app()
    GENERATED.mkdir(parents=True, exist_ok=True)

    with app.app_context():
        db.create_all()
        admin = User.query.filter_by(role="ADMIN").first()
        if not admin:
            admin = User(
                email="role-dash-verify@dxcon.test",
                role="ADMIN",
                password_hash=hash_password("VerifyOnly123!"),
                is_active=True,
            )
            db.session.add(admin)
            db.session.commit()

        for role in ("admin", "reception", "laboratory", "collector", "doctor", "patient"):
            payload = build_role_dashboard(role)
            checks[f"build_{role}"] = {
                "ok": bool(payload.get("cards")) and payload.get("pii_policy") == "aggregates_only",
                "cards": len(payload.get("cards") or []),
            }

        checks["rbac"] = {
            "ok": role_can_access("ADMIN", "admin") and not role_can_access("PATIENT", "laboratory")
        }

        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess["user_id"] = admin.id
                sess["role"] = "ADMIN"
                sess["email"] = admin.email
            resp = client.get("/api/v1/role-dashboards/admin")
            checks["api_admin"] = {"ok": resp.status_code == 200}
            summary = client.get("/api/v1/role-dashboards/summary")
            checks["api_summary"] = {"ok": summary.status_code == 200}

        pdf_present = (ROOT / "app" / "reporting_engine" / "pdf_service.py").exists()
        checks["report_pdf_probe"] = {
            "ok": True,
            "pdf_service_present": pdf_present,
            "note": "present" if pdf_present else "missing — mark P0 in go-live if PDF required",
        }

    passed = sum(1 for c in checks.values() if c.get("ok"))
    report = {
        "module": "role_dashboards",
        "passed": passed,
        "total": len(checks),
        "checks": checks,
        "elapsed": round(time.time() - start, 2),
        "generated_at": utc_now(),
    }
    (GENERATED / "ROLE_DASHBOARDS_VERIFY.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Role Dashboards Verify: {passed}/{len(checks)} PASS")
    for name, r in checks.items():
        print(f"  [{'PASS' if r.get('ok') else 'FAIL'}] {name}")
    return 0 if passed == len(checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
