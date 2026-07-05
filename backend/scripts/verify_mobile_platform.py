#!/usr/bin/env python3
"""Verify Mobile Platform Phase 7.4."""

from __future__ import annotations

import json, os, sys, time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = ROOT / "generated_release" / "MOBILE_PLATFORM_REPORT.json"

WEB_ROUTES = ('/mobile-platform', '/mobile-platform/collector-api', '/mobile-platform/doctor-api', '/mobile-platform/patient-api', '/mobile-platform/notifications', '/mobile-platform/offline-sync', '/mobile-platform/token-refresh', '/mobile-platform/conflict-resolution', '/mobile-platform/pwa-manifest')
API_ROUTES = ('/api/v1/mobile-platform/dashboard', '/api/v1/mobile-platform/collector-api', '/api/v1/mobile-platform/doctor-api', '/api/v1/mobile-platform/patient-api', '/api/v1/mobile-platform/notifications', '/api/v1/mobile-platform/offline-sync', '/api/v1/mobile-platform/token-refresh', '/api/v1/mobile-platform/conflict-resolution', '/api/v1/mobile-platform/pwa-manifest', '/api/v1/mobile-platform/readiness')


def utc_now():
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
    print("\n=== DXCON MOBILE PLATFORM VERIFY ===\n")
    start = time.perf_counter()
    checks = {}
    from app import create_app
    app = create_app()
    with app.app_context():
        from app.core.passwords import hash_password
        from app.extensions.db import db
        from app.models.user import User
        from app.services.mobile_platform_service import FEATURES, ensure_mobile_platform
        db.create_all()
        if not User.query.filter(User.role.in_(("SUPER_ADMIN", "ADMIN"))).first():
            db.session.add(User(email="verify-mobile_platform@demo.dxcon.test", role="ADMIN", password_hash=hash_password("DemoPass123!"), is_active=True))
            db.session.commit()
        ensure_mobile_platform()
        routes = {str(r.rule) for r in app.url_map.iter_rules()}
        missing_web = [r for r in WEB_ROUTES if r not in routes]
        missing_api = [r for r in API_ROUTES if r not in routes]
        checks["route_registry"] = {"ok": not missing_web and not missing_api, "missing_web": missing_web, "missing_api": missing_api}
        client = app.test_client()
        checks["auth"] = {"ok": _login_admin(client)}
        web_ok = all((client.get(r, follow_redirects=True).status_code == 200) for r in WEB_ROUTES)
        checks["web_pages"] = {"ok": web_ok}
        api_ok = all((client.get(r, follow_redirects=True).status_code == 200) for r in API_ROUTES)
        checks["api_endpoints"] = {"ok": api_ok}
        dash = _api_json(client.get("/api/v1/mobile-platform/dashboard"))
        checks["feature_coverage"] = {"ok": len(dash.get("features", [])) == 8 and list(FEATURES) == dash.get("features")}
        checks["legacy_0"] = {"ok": client.get("/api/v1/collector/jobs", follow_redirects=True).status_code == 200}
        checks["legacy_1"] = {"ok": "/api/v1/auth/refresh" in routes and client.post("/api/v1/auth/refresh", json={}).status_code != 404}

    passed = sum(1 for c in checks.values() if c.get("ok"))
    total = len(checks)
    score = round((passed / total) * 100, 1) if total else 0
    report = {"generated_at": utc_now(), "phase": "7.4", "sprint": "Mobile Platform", "summary": {"score": score, "checks_passed": passed, "checks_total": total, "ok": passed == total, "runtime_seconds": round(time.perf_counter() - start, 3)}, "checks": checks}
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    print(f"Mobile Platform score: {score}% ({passed}/{total})")
    print("PASS\n" if report["summary"]["ok"] else "FAIL\n")
    return 0 if report["summary"]["ok"] else 1

if __name__ == "__main__":
    raise SystemExit(main())
