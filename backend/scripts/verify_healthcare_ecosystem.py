#!/usr/bin/env python3
"""Verify Healthcare Ecosystem Phase 10 and generate v1.0.0-rc1 release artifacts."""

from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
GENERATED = ROOT / "generated_release"
VERIFY_PATH = GENERATED / "HEALTHCARE_ECOSYSTEM_REPORT.json"
SYSTEM_READINESS_PATH = GENERATED / "SYSTEM_READINESS_REPORT.json"
GO_LIVE_PATH = GENERATED / "GO_LIVE_REPORT.json"
COMMERCIAL_PATH = GENERATED / "COMMERCIAL_READINESS_REPORT.json"
CERT_PATH = GENERATED / "ENTERPRISE_CERTIFICATION_REPORT.json"
SUMMARY_PATH = GENERATED / "PHASE10_RELEASE_SUMMARY.json"

ENTERPRISE_DOCS = (
    REPO / "docs" / "SYSTEM_ARCHITECTURE.md",
    REPO / "docs" / "OPERATIONS_GUIDE.md",
    REPO / "docs" / "DEPLOYMENT_GUIDE.md",
    REPO / "docs" / "SUPPORT_GUIDE.md",
    REPO / "docs" / "CUSTOMER_GUIDE.md",
    REPO / "docs" / "PARTNER_GUIDE.md",
    REPO / "docs" / "GO_LIVE_RUNBOOK.md",
    REPO / "docs" / "BACKUP_RUNBOOK.md",
    REPO / "docs" / "RESTORE_RUNBOOK.md",
    REPO / "docs" / "ROLLBACK_RUNBOOK.md",
    REPO / "docs" / "KNOWN_LIMITATIONS.md",
    REPO / "docs" / "ROADMAP_v2.md",
)

HEALTH_ROUTES = (
    "/live",
    "/ready",
    "/api/v1/system/health",
    "/api/v1/system/liveness",
)

DASHBOARD_ROUTES = (
    "/healthcare-ecosystem",
    "/intelligent-healthcare",
    "/regional-cloud",
    "/monitoring",
)

API_ROUTES_SAMPLE = (
    "/api/v1/healthcare-ecosystem/dashboard",
    "/api/v1/healthcare-ecosystem/readiness",
    "/api/v1/system/routes",
    "/api/v1/system/stats",
)


def _routes_from_file(path: Path) -> list[str]:
    routes: list[str] = []
    for line in path.read_text().splitlines():
        if '.route("' in line:
            routes.append(line.split('.route("')[1].split('"')[0])
    return list(dict.fromkeys(routes))


WEB_ROUTES = _routes_from_file(ROOT / "app" / "web" / "healthcare_ecosystem.py")
HUB_API_ROUTES = [f"/api/v1/healthcare-ecosystem{route}" for route in _routes_from_file(ROOT / "app" / "api" / "healthcare_ecosystem" / "routes.py")]


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

    print("\n=== DXCON HEALTHCARE ECOSYSTEM PHASE 10 VERIFY ===\n")
    start = time.perf_counter()
    checks: dict[str, dict] = {}

    from app import create_app

    app = create_app()
    with app.app_context():
        from app.core.passwords import hash_password
        from app.extensions.db import db
        from app.models.user import User
        from app.services.healthcare_ecosystem_service import (
            FEATURES,
            RELEASE,
            commercial_readiness_report,
            ensure_healthcare_ecosystem,
            enterprise_certification_report,
            go_live_report,
            healthcare_ecosystem_readiness_report,
            phase10_release_summary,
            system_readiness_report,
        )

        db.create_all()
        if not User.query.filter(User.role.in_(("SUPER_ADMIN", "ADMIN"))).first():
            db.session.add(
                User(
                    email="verify-healthcare-ecosystem@demo.dxcon.test",
                    role="ADMIN",
                    password_hash=hash_password("DemoPass123!"),
                    is_active=True,
                )
            )
            db.session.commit()

        ensure_healthcare_ecosystem()
        routes = {str(r.rule) for r in app.url_map.iter_rules()}
        missing_web = [r for r in WEB_ROUTES if r not in routes]
        missing_api = [r for r in HUB_API_ROUTES if r not in routes]
        checks["route_registry"] = {"ok": not missing_web and not missing_api, "missing_web": missing_web, "missing_api": missing_api}
        checks["enterprise_docs"] = {"ok": all(p.exists() for p in ENTERPRISE_DOCS), "count": sum(1 for p in ENTERPRISE_DOCS if p.exists())}

        client = app.test_client()
        checks["auth"] = {"ok": _login_admin(client)}
        checks["web_pages"] = {"ok": all(client.get(r, follow_redirects=True).status_code == 200 for r in WEB_ROUTES)}
        checks["hub_api"] = {"ok": all(client.get(r, follow_redirects=True).status_code == 200 for r in HUB_API_ROUTES)}

        dash = _api_json(client.get("/api/v1/healthcare-ecosystem/dashboard"))
        checks["feature_coverage"] = {
            "ok": len(dash.get("features", [])) == 25 and list(FEATURES) == dash.get("features"),
        }
        checks["release_tag"] = {"ok": dash.get("release", {}).get("tag") == "v1.0.0-rc1"}

        checks["health_verification"] = {
            "ok": all(client.get(r, follow_redirects=True).status_code == 200 for r in HEALTH_ROUTES),
        }
        checks["dashboard_verification"] = {
            "ok": all(client.get(r, follow_redirects=True).status_code == 200 for r in DASHBOARD_ROUTES),
        }
        checks["api_verification"] = {
            "ok": all(client.get(r, follow_redirects=True).status_code == 200 for r in API_ROUTES_SAMPLE),
        }
        checks["pilot_hub"] = {"ok": client.get("/pilot-toolkit", follow_redirects=True).status_code == 200}
        checks["readiness_hub"] = {"ok": client.get("/readiness-pack", follow_redirects=True).status_code == 200}

        system_report = system_readiness_report()
        go_live = go_live_report()
        commercial = commercial_readiness_report()
        certification = enterprise_certification_report()
        summary = phase10_release_summary()
        GENERATED.mkdir(parents=True, exist_ok=True)
        SYSTEM_READINESS_PATH.write_text(json.dumps(system_report, indent=2, default=str), encoding="utf-8")
        GO_LIVE_PATH.write_text(json.dumps(go_live, indent=2, default=str), encoding="utf-8")
        COMMERCIAL_PATH.write_text(json.dumps(commercial, indent=2, default=str), encoding="utf-8")
        CERT_PATH.write_text(json.dumps(certification, indent=2, default=str), encoding="utf-8")
        SUMMARY_PATH.write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")

        checks["system_readiness_report"] = {"ok": system_report.get("release", {}).get("tag") == RELEASE["tag"]}
        checks["go_live_report"] = {"ok": go_live.get("go_live_ready") is True}
        checks["commercial_readiness_report"] = {"ok": commercial.get("commercial_ready") is True}
        checks["enterprise_certification_report"] = {"ok": certification.get("recommended_tag") == RELEASE["tag"]}

    passed = sum(1 for c in checks.values() if c.get("ok"))
    total = len(checks)
    score = round((passed / total) * 100, 1) if total else 0
    report = {
        "generated_at": utc_now(),
        "phase": "10",
        "sprint": "Healthcare Ecosystem",
        "release": RELEASE,
        "summary": {
            "score": score,
            "checks_passed": passed,
            "checks_total": total,
            "ok": passed == total,
            "runtime_seconds": round(time.perf_counter() - start, 3),
            "recommended_tag": "v1.0.0-rc1",
        },
        "checks": checks,
    }
    VERIFY_PATH.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    print(f"Healthcare Ecosystem score: {score}% ({passed}/{total})")
    print(f"Release candidate tag: {RELEASE['tag']}")
    print("PASS\n" if report["summary"]["ok"] else "FAIL\n")
    return 0 if report["summary"]["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
