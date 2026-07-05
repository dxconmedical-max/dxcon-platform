#!/usr/bin/env python3
"""Verify Regional Cloud Platform Phase 9."""

from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
READINESS_PATH = ROOT / "generated_release" / "REGIONAL_READINESS_REPORT.json"
DEPLOYMENT_PATH = ROOT / "generated_release" / "DEPLOYMENT_REPORT.json"
VERIFY_PATH = ROOT / "generated_release" / "REGIONAL_CLOUD_REPORT.json"
ARCH_DOCS = (
    REPO / "docs" / "architecture" / "REGIONAL_ARCHITECTURE.md",
    REPO / "docs" / "architecture" / "DEPLOYMENT_ARCHITECTURE.md",
    REPO / "docs" / "COMPLIANCE_GUIDE.md",
)


def _routes_from_file(path: Path) -> list[str]:
    routes: list[str] = []
    for line in path.read_text().splitlines():
        if '.route("' in line:
            routes.append(line.split('.route("')[1].split('"')[0])
    return list(dict.fromkeys(routes))


WEB_ROUTES = _routes_from_file(ROOT / "app" / "web" / "regional_cloud.py")
API_ROUTES = [f"/api/v1/regional-cloud{route}" for route in _routes_from_file(ROOT / "app" / "api" / "regional_cloud" / "routes.py")]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _login_admin(client):
    from app.models.user import User

    user = User.query.filter(User.role == "SUPER_ADMIN").first() or User.query.filter(User.role == "ADMIN").first()
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
        print("FAIL: DATABASE_URL required", file=sys.stderr)
        return 1

    print("\n=== DXCON REGIONAL CLOUD PLATFORM VERIFY ===\n")
    start = time.perf_counter()
    checks: dict[str, dict] = {}

    from app import create_app

    app = create_app()
    with app.app_context():
        from app.core.passwords import hash_password
        from app.extensions.db import db
        from app.models.user import User
        from app.services.regional_cloud_service import (
            FEATURES,
            GOVERNANCE,
            ensure_regional_cloud,
            regional_cloud_deployment_report,
            regional_cloud_readiness_report,
        )

        db.create_all()
        if not User.query.filter(User.role.in_(("SUPER_ADMIN", "ADMIN"))).first():
            db.session.add(
                User(
                    email="verify-regional-cloud@demo.dxcon.test",
                    role="ADMIN",
                    password_hash=hash_password("DemoPass123!"),
                    is_active=True,
                )
            )
            db.session.commit()

        ensure_regional_cloud()
        routes = {str(r.rule) for r in app.url_map.iter_rules()}
        missing_web = [r for r in WEB_ROUTES if r not in routes]
        missing_api = [r for r in API_ROUTES if r not in routes]
        checks["route_registry"] = {"ok": not missing_web and not missing_api, "missing_web": missing_web, "missing_api": missing_api}
        checks["architecture_docs"] = {"ok": all(p.exists() for p in ARCH_DOCS), "paths": [str(p.relative_to(REPO)) for p in ARCH_DOCS]}

        client = app.test_client()
        checks["auth"] = {"ok": _login_admin(client)}
        checks["web_pages"] = {"ok": all(client.get(r, follow_redirects=True).status_code == 200 for r in WEB_ROUTES)}
        checks["api_endpoints"] = {"ok": all(client.get(r, follow_redirects=True).status_code == 200 for r in API_ROUTES)}

        dash = _api_json(client.get("/api/v1/regional-cloud/dashboard"))
        checks["feature_coverage"] = {
            "ok": len(dash.get("features", [])) == 28 and list(FEATURES) == dash.get("features"),
        }
        checks["governance"] = {
            "ok": GOVERNANCE["backward_compatible"] and not GOVERNANCE["destructive_migrations"],
        }
        checks["legacy_production"] = {"ok": client.get("/production-deployment", follow_redirects=True).status_code == 200}
        checks["legacy_federation"] = {"ok": client.get("/federation-platform", follow_redirects=True).status_code == 200}
        checks["legacy_backup"] = {"ok": client.get("/backup-recovery", follow_redirects=True).status_code == 200}

        readiness = regional_cloud_readiness_report()
        deployment = regional_cloud_deployment_report()
        READINESS_PATH.parent.mkdir(parents=True, exist_ok=True)
        READINESS_PATH.write_text(json.dumps(readiness, indent=2, default=str), encoding="utf-8")
        DEPLOYMENT_PATH.write_text(json.dumps(deployment, indent=2, default=str), encoding="utf-8")
        checks["readiness_report"] = {"ok": readiness.get("phase") == "9" and len(readiness.get("features", [])) == 28}
        checks["deployment_report"] = {"ok": deployment.get("phase") == "9" and len(deployment.get("providers", [])) == 5}

    passed = sum(1 for c in checks.values() if c.get("ok"))
    total = len(checks)
    score = round((passed / total) * 100, 1) if total else 0
    report = {
        "generated_at": utc_now(),
        "phase": "9",
        "sprint": "Regional Cloud Platform",
        "summary": {
            "score": score,
            "checks_passed": passed,
            "checks_total": total,
            "ok": passed == total,
            "runtime_seconds": round(time.perf_counter() - start, 3),
        },
        "checks": checks,
    }
    VERIFY_PATH.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    print(f"Regional Cloud score: {score}% ({passed}/{total})")
    print("PASS\n" if report["summary"]["ok"] else "FAIL\n")
    return 0 if report["summary"]["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
