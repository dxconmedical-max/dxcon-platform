#!/usr/bin/env python3
"""Verify Launch UI Sprint 1 routes and generate LAUNCH_UI_REPORT.json."""

from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "generated_release"
REPORT_PATH = GENERATED / "LAUNCH_UI_REPORT.json"

PUBLIC_ROUTES = (
    "/home",
    "/login",
    "/health",
    "/ready",
)

APP_ROUTES = (
    "/app/executive",
    "/app/reception",
    "/app/doctor",
    "/app/lab",
    "/app/collector",
    "/app/patient",
    "/app/system",
    "/executive-v10",
)


def _routes_from_file(path: Path) -> list[str]:
    routes: list[str] = []
    for line in path.read_text().splitlines():
        if '.route("' in line:
            routes.append(line.split('.route("')[1].split('"')[0])
    return list(dict.fromkeys(routes))


WEB_ROUTES = _routes_from_file(ROOT / "app" / "web" / "launch_ui.py")


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


def _page_ok(client, path: str, *, follow: bool = True) -> bool:
    response = client.get(path, follow_redirects=follow)
    if path in {"/health", "/ready"}:
        return response.status_code in {200, 503}
    if response.status_code != 200:
        return False
    body = (response.get_data(as_text=True) or "").lower()
    return "dxcon" in body or "launch-" in body


def main() -> int:
    sys.path.insert(0, str(ROOT))
    os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

    print("\n=== DXCON LAUNCH UI SPRINT 1 VERIFY ===\n")
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
                    email="verify-launch-ui@demo.dxcon.test",
                    role="ADMIN",
                    password_hash=hash_password("DemoPass123!"),
                    is_active=True,
                )
            )
            db.session.commit()

        routes = {str(r.rule) for r in app.url_map.iter_rules()}
        missing_web = [r for r in WEB_ROUTES if r not in routes]
        checks["route_registry"] = {
            "ok": not missing_web,
            "missing": missing_web,
            "registered": WEB_ROUTES,
        }

        client = app.test_client()

        root = client.get("/", follow_redirects=False)
        checks["root_redirect"] = {
            "ok": root.status_code in {302, 303, 307, 308}
            and "/login" in (root.headers.get("Location") or ""),
            "status_code": root.status_code,
            "location": root.headers.get("Location"),
        }

        public_results = {}
        for path in PUBLIC_ROUTES:
            public_results[path] = {
                "status_code": client.get(path, follow_redirects=True).status_code,
                "ok": _page_ok(client, path),
            }
        checks["public_pages"] = {
            "ok": all(item["ok"] for item in public_results.values()),
            "routes": public_results,
        }

        checks["auth"] = {"ok": _login_admin(client)}

        app_results = {}
        for path in APP_ROUTES:
            response = client.get(path, follow_redirects=True)
            app_results[path] = {
                "status_code": response.status_code,
                "ok": response.status_code == 200 and "launch-shell" in (response.get_data(as_text=True) or ""),
            }
        checks["app_pages"] = {
            "ok": all(item["ok"] for item in app_results.values()),
            "routes": app_results,
        }

        login_html = client.get("/login").get_data(as_text=True)
        checks["login_shell"] = {
            "ok": "launch-login-card" in login_html and "Sign in" in login_html,
        }
        checks["marketing_shell"] = {
            "ok": "launch-marketing-hero" in client.get("/home").get_data(as_text=True),
        }

        passed = sum(1 for item in checks.values() if item.get("ok"))
        total = len(checks)
        elapsed = round(time.perf_counter() - start, 2)

        report = {
            "sprint": "Launch UI Sprint 1",
            "generated_at": utc_now(),
            "elapsed_seconds": elapsed,
            "checks": checks,
            "routes": {
                "public": list(PUBLIC_ROUTES),
                "app": list(APP_ROUTES),
                "launch_ui_blueprint": WEB_ROUTES,
            },
            "summary": {
                "passed": passed,
                "total": total,
                "ok": passed == total,
            },
        }

        GENERATED.mkdir(parents=True, exist_ok=True)
        REPORT_PATH.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")

        for name, payload in checks.items():
            print(f"{'PASS' if payload.get('ok') else 'FAIL'}: {name}")
            if not payload.get("ok"):
                for key, value in payload.items():
                    if key != "ok" and value:
                        print(f"  {key}: {value}")

        print(f"\nSummary: {passed}/{total} passed in {elapsed}s")
        print(f"Report: {REPORT_PATH}\n")
        return 0 if report["summary"]["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
