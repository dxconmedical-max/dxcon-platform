#!/usr/bin/env python3
"""Verify Intelligent Healthcare Platform Phase 8."""

from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
READINESS_PATH = ROOT / "generated_release" / "AI_READINESS_REPORT.json"
GOVERNANCE_PATH = ROOT / "generated_release" / "AI_GOVERNANCE_REPORT.json"
VERIFY_PATH = ROOT / "generated_release" / "INTELLIGENT_HEALTHCARE_REPORT.json"
ARCH_DOCS = (
    REPO / "docs" / "architecture" / "AI_ARCHITECTURE.md",
    REPO / "docs" / "architecture" / "AI_SEQUENCE_DIAGRAMS.md",
    REPO / "docs" / "architecture" / "AI_COMPONENTS.md",
    REPO / "docs" / "MEDICAL_AI_GUIDE.md",
)


def _routes_from_file(path: Path) -> list[str]:
    routes: list[str] = []
    for line in path.read_text().splitlines():
        if '.route("' in line:
            routes.append(line.split('.route("')[1].split('"')[0])
    return list(dict.fromkeys(routes))


WEB_ROUTES = _routes_from_file(ROOT / "app" / "web" / "intelligent_healthcare.py")
API_ROUTES = [f"/api/v1/intelligent-healthcare{route}" for route in _routes_from_file(ROOT / "app" / "api" / "intelligent_healthcare" / "routes.py")]


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

    print("\n=== DXCON INTELLIGENT HEALTHCARE PLATFORM VERIFY ===\n")
    start = time.perf_counter()
    checks: dict[str, dict] = {}

    from app import create_app

    app = create_app()
    with app.app_context():
        from app.core.passwords import hash_password
        from app.extensions.db import db
        from app.models.user import User
        from app.services.intelligent_healthcare_service import (
            FEATURES,
            GOVERNANCE_POLICY,
            ensure_intelligent_healthcare,
            intelligent_healthcare_governance_report,
            intelligent_healthcare_readiness_report,
        )

        db.create_all()
        if not User.query.filter(User.role.in_(("SUPER_ADMIN", "ADMIN"))).first():
            db.session.add(
                User(
                    email="verify-intelligent-healthcare@demo.dxcon.test",
                    role="ADMIN",
                    password_hash=hash_password("DemoPass123!"),
                    is_active=True,
                )
            )
            db.session.commit()

        ensure_intelligent_healthcare()
        routes = {str(r.rule) for r in app.url_map.iter_rules()}
        missing_web = [r for r in WEB_ROUTES if r not in routes]
        missing_api = [r for r in API_ROUTES if r not in routes]
        checks["route_registry"] = {"ok": not missing_web and not missing_api, "missing_web": missing_web, "missing_api": missing_api}

        checks["architecture_docs"] = {"ok": all(p.exists() for p in ARCH_DOCS), "paths": [str(p.relative_to(REPO)) for p in ARCH_DOCS]}

        client = app.test_client()
        checks["auth"] = {"ok": _login_admin(client)}
        checks["web_pages"] = {"ok": all(client.get(r, follow_redirects=True).status_code == 200 for r in WEB_ROUTES)}
        checks["api_endpoints"] = {"ok": all(client.get(r, follow_redirects=True).status_code == 200 for r in API_ROUTES)}

        dash = _api_json(client.get("/api/v1/intelligent-healthcare/dashboard"))
        checks["feature_coverage"] = {
            "ok": len(dash.get("features", [])) == 31 and list(FEATURES) == dash.get("features"),
        }
        checks["governance_policy"] = {
            "ok": GOVERNANCE_POLICY["human_review_required"] and not GOVERNANCE_POLICY["automatic_diagnosis"],
        }
        checks["legacy_ai_clinical"] = {"ok": client.get("/ai-clinical", follow_redirects=True).status_code == 200}
        checks["legacy_ai_copilot"] = {"ok": client.get("/ai-copilot", follow_redirects=True).status_code == 200}
        checks["legacy_ai_operations"] = {"ok": client.get("/api/v1/ai-operations/dashboard", follow_redirects=True).status_code == 200}

        readiness = intelligent_healthcare_readiness_report()
        governance = intelligent_healthcare_governance_report()
        READINESS_PATH.parent.mkdir(parents=True, exist_ok=True)
        READINESS_PATH.write_text(json.dumps(readiness, indent=2, default=str), encoding="utf-8")
        GOVERNANCE_PATH.write_text(json.dumps(governance, indent=2, default=str), encoding="utf-8")
        checks["readiness_report"] = {"ok": readiness.get("phase") == "8" and len(readiness.get("features", [])) == 31}
        checks["governance_report"] = {"ok": governance.get("human_review_mandatory") is True}

    passed = sum(1 for c in checks.values() if c.get("ok"))
    total = len(checks)
    score = round((passed / total) * 100, 1) if total else 0
    report = {
        "generated_at": utc_now(),
        "phase": "8",
        "sprint": "Intelligent Healthcare Platform",
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
    print(f"Intelligent Healthcare score: {score}% ({passed}/{total})")
    print("PASS\n" if report["summary"]["ok"] else "FAIL\n")
    return 0 if report["summary"]["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
