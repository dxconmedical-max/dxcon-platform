#!/usr/bin/env python3
"""Verify production web gateway — Sprint 011."""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "generated_release"
sys.path.insert(0, str(ROOT))

WORKSPACE_ROUTES = (
    "/app",
    "/app/admin",
    "/app/executive",
    "/app/reception",
    "/app/doctor",
    "/app/lab",
    "/app/collector",
    "/app/clinic",
    "/app/patient",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def fetch(url: str, timeout_s: int = 10) -> dict:
    try:
        req = Request(url, headers={"User-Agent": "dxcon-web-gateway-verify/1.0"})
        with urlopen(req, timeout=timeout_s) as resp:
            body = resp.read(512).decode("utf-8", errors="replace")
            return {"ok": 200 <= resp.status < 300, "status": resp.status, "sample": body[:120]}
    except HTTPError as exc:
        return {"ok": False, "status": exc.code, "error": str(exc)}
    except URLError as exc:
        return {"ok": False, "status": None, "error": str(exc)}
    except Exception as exc:
        return {"ok": False, "status": None, "error": str(exc)}


def main() -> int:
    os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
    from app import create_app
    from app.core.passwords import hash_password
    from app.extensions.db import db
    from app.models.user import User
    from app.web_gateway.config import domain_configuration_report
    from app.web_gateway.routing import ROLE_WORKSPACE_ROUTES, workspace_path_for_role

    app = create_app()
    app.config.update(
        {
            "TESTING": True,
            "DEMO_MODE": True,
            "PUBLIC_SITE_URL": os.environ.get("PUBLIC_SITE_URL", "https://dxcon.com.vn"),
            "WEB_APP_URL": os.environ.get("WEB_APP_URL", "https://app.dxcon.com.vn"),
            "API_BASE_URL": os.environ.get("API_BASE_URL", "https://api.dxcon.com.vn"),
        }
    )

    findings = []
    checks = {}

    with app.app_context():
        db.create_all()
        admin = User.query.filter_by(email="gateway-admin@dxcon.test").first()
        if not admin:
            admin = User(
                email="gateway-admin@dxcon.test",
                role="SUPER_ADMIN",
                password_hash=hash_password("VerifyOnly123!"),
                is_active=True,
            )
            db.session.add(admin)
            db.session.commit()

        client = app.test_client()

        with client.session_transaction() as sess:
            sess.clear()
        login_resp = client.get("/login")
        checks["login_page"] = {
            "ok": login_resp.status_code == 200 and "launch-login-card" in login_resp.get_data(as_text=True),
            "status": login_resp.status_code,
        }

        home_resp = client.get("/home")
        checks["landing_page"] = {
            "ok": home_resp.status_code == 200 and "launch-marketing-hero" in home_resp.get_data(as_text=True),
            "status": home_resp.status_code,
        }

        with client.session_transaction() as sess:
            sess["user_id"] = admin.id
            sess["role"] = admin.role
            sess["email"] = admin.email

        workspace_results = {}
        for route in WORKSPACE_ROUTES:
            resp = client.get(route, follow_redirects=True)
            body = resp.get_data(as_text=True)
            workspace_results[route] = {
                "status": resp.status_code,
                "ok": resp.status_code == 200 and "launch-shell" in body,
            }
        checks["workspace_routes"] = {
            "ok": all(r["ok"] for r in workspace_results.values()),
            "routes": workspace_results,
        }

        checks["role_routing_map"] = {
            "ok": len(ROLE_WORKSPACE_ROUTES) >= 10,
            "count": len(ROLE_WORKSPACE_ROUTES),
            "sample": {k: workspace_path_for_role(k) for k in ("SUPER_ADMIN", "DOCTOR", "PATIENT")},
        }

        cfg = domain_configuration_report()
        checks["api_base_url_configured"] = {
            "ok": bool(cfg.get("api_base_url")),
            "value": cfg.get("api_base_url"),
        }

        api_js = client.get("/static/js/dxcon-api-client.js")
        checks["api_client_js"] = {"ok": api_js.status_code == 200 and b"DxConApiClient" in api_js.data}

        docs_path = ROOT.parent / "docs" / "DOMAIN_SETUP_DXCON.md"
        checks["domain_docs"] = {"ok": docs_path.exists(), "path": str(docs_path)}

    api_base = os.environ.get("API_BASE_URL", "https://api.dxcon.com.vn").rstrip("/")
    health = fetch(f"{api_base}/health")
    external = {
        "url": f"{api_base}/health",
        "result": health,
        "status": "PASS" if health.get("ok") else "WARNING",
    }
    if not health.get("ok"):
        external["detail"] = "External API check skipped or unreachable — WARNING for local runs"

    gateway_report = {
        "generated_at": utc_now(),
        "sprint": "011-production-web-gateway",
        "checks": checks,
        "external_api_health": external,
        "ok": all(c.get("ok") for c in checks.values()),
    }
    domain_report = {
        "generated_at": utc_now(),
        "configuration": cfg,
        "supported_domains": cfg.get("supported_domains", []),
        "legacy_api_host": "dxcon-ap.onrender.com",
    }

    GENERATED.mkdir(parents=True, exist_ok=True)
    (GENERATED / "PRODUCTION_WEB_GATEWAY_REPORT.json").write_text(
        json.dumps(gateway_report, indent=2), encoding="utf-8"
    )
    (GENERATED / "DOMAIN_CONFIGURATION_REPORT.json").write_text(
        json.dumps(domain_report, indent=2), encoding="utf-8"
    )

    for name, result in checks.items():
        findings.append({"name": name, "ok": result.get("ok"), "detail": result})

    fails = sum(1 for f in findings if not f["ok"])
    print(f"Production web gateway: {'PASS' if fails == 0 else 'FAIL'} ({fails} failed checks)")
    print(f"External API health: {external['status']} ({external['url']})")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
