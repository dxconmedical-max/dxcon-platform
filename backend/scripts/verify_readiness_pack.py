#!/usr/bin/env python3
"""Verify Readiness Pack Phase 5 Sprint 5.14."""

from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
REPORT_PATH = ROOT / "generated_release" / "READINESS_PACK_REPORT.json"

WEB_ROUTES = (
    "/readiness-pack",
    "/readiness-pack/system",
    "/readiness-pack/security",
    "/readiness-pack/pilot",
    "/readiness-pack/go-live-checklist",
    "/readiness-pack/limitations",
    "/readiness-pack/roadmap",
)

API_ROUTES = (
    "/api/v1/readiness-pack/dashboard",
    "/api/v1/readiness-pack/system",
    "/api/v1/readiness-pack/security",
    "/api/v1/readiness-pack/pilot",
    "/api/v1/readiness-pack/go-live-checklist",
    "/api/v1/readiness-pack/limitations",
    "/api/v1/readiness-pack/roadmap",
    "/api/v1/readiness-pack/inventory",
    "/api/v1/readiness-pack/readiness",
)

ARTIFACT_FILES = (
    "SYSTEM_READINESS_REPORT.json",
    "SECURITY_READINESS_REPORT.json",
    "PILOT_READINESS_REPORT.json",
    "GO_LIVE_CHECKLIST.json",
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

    print("\n=== DXCON READINESS PACK VERIFY ===\n")
    start = time.perf_counter()
    checks: dict[str, dict] = {}

    from app import create_app

    app = create_app()
    with app.app_context():
        from app.core.passwords import hash_password
        from app.extensions.db import db
        from app.models.user import User
        from app.services.readiness_pack_service import FEATURES, write_generated_artifacts

        db.create_all()
        if not User.query.filter(User.role.in_(("SUPER_ADMIN", "ADMIN"))).first():
            db.session.add(
                User(
                    email="verify-readiness-pack@demo.dxcon.test",
                    role="ADMIN",
                    password_hash=hash_password("DemoPass123!"),
                    is_active=True,
                )
            )
            db.session.commit()

        write_generated_artifacts()

        routes = {str(rule.rule) for rule in app.url_map.iter_rules()}
        missing_web = [route for route in WEB_ROUTES if route not in routes]
        missing_api = [route for route in API_ROUTES if route not in routes]
        checks["route_registry"] = {
            "ok": not missing_web and not missing_api,
            "missing_web": missing_web,
            "missing_api": missing_api,
        }

        doc_checks = {
            "KNOWN_LIMITATIONS.md": (REPO / "docs" / "KNOWN_LIMITATIONS.md").exists(),
            "ROADMAP_v2.md": (REPO / "docs" / "ROADMAP_v2.md").exists(),
        }
        checks["documentation_files"] = {"ok": all(doc_checks.values()), "files": doc_checks}

        artifact_checks = {
            name: (ROOT / "generated_release" / name).exists() for name in ARTIFACT_FILES
        }
        checks["generated_artifacts"] = {"ok": all(artifact_checks.values()), "files": artifact_checks}

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
        checks["readiness_pack_dashboard"] = {"ok": web_ok, "routes": web_results}

        api_ok = True
        api_results = {}
        for route in API_ROUTES:
            response = client.get(route, follow_redirects=True)
            ok = response.status_code == 200
            api_ok = api_ok and ok
            api_results[route] = {"status_code": response.status_code, "ok": ok}
        checks["api_endpoints"] = {"ok": api_ok, "routes": api_results}

        dashboard = _api_json(client.get("/api/v1/readiness-pack/dashboard"))
        checks["feature_coverage"] = {
            "ok": len(dashboard.get("features", [])) == 6 and list(FEATURES) == dashboard.get("features"),
            "features": len(FEATURES),
        }

        checks["system_readiness"] = {
            "ok": "summary" in _api_json(client.get("/api/v1/readiness-pack/system")),
        }
        checks["security_readiness"] = {
            "ok": _api_json(client.get("/api/v1/readiness-pack/security")).get("exists") is True,
        }
        checks["pilot_readiness"] = {
            "ok": _api_json(client.get("/api/v1/readiness-pack/pilot")).get("exists") is True,
        }
        checks["go_live_checklist"] = {
            "ok": _api_json(client.get("/api/v1/readiness-pack/go-live-checklist")).get("items_total", 0) >= 1,
        }
        limitations = _api_json(client.get("/api/v1/readiness-pack/limitations"))
        checks["known_limitations"] = {
            "ok": limitations.get("exists") is True and len(limitations.get("content", "")) > 100,
        }
        roadmap = _api_json(client.get("/api/v1/readiness-pack/roadmap"))
        checks["roadmap_v2"] = {
            "ok": roadmap.get("exists") is True and len(roadmap.get("content", "")) > 100,
        }

        legacy_checklist = client.get("/pilot-checklist", follow_redirects=True)
        checks["legacy_pilot_checklist_preserved"] = {"ok": legacy_checklist.status_code == 200}

        legacy_security = client.get("/security-compliance", follow_redirects=True)
        checks["legacy_security_compliance_preserved"] = {"ok": legacy_security.status_code == 200}

        legacy_monitoring = client.get("/monitoring", follow_redirects=True)
        checks["legacy_monitoring_preserved"] = {"ok": legacy_monitoring.status_code == 200}

    passed = sum(1 for item in checks.values() if item.get("ok"))
    total = len(checks)
    score = round((passed / total) * 100, 1) if total else 0.0
    report = {
        "generated_at": utc_now(),
        "phase": "5.14",
        "sprint": "Readiness Pack",
        "summary": {
            "score": score,
            "checks_passed": passed,
            "checks_total": total,
            "ok": passed == total,
            "runtime_seconds": round(time.perf_counter() - start, 3),
        },
        "checks": checks,
        "readiness": _api_json(client.get("/api/v1/readiness-pack/readiness")) if "client" in locals() else {},
    }
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")

    print(f"Readiness Pack score: {score}%")
    print(f"Checks passed: {passed}/{total}")
    print(f"Report: {REPORT_PATH}")
    if report["summary"]["ok"]:
        print("READINESS PACK VERIFY PASS\n")
        return 0
    print("READINESS PACK VERIFY FAIL\n")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
