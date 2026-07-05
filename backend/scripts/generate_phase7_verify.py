#!/usr/bin/env python3
"""Generate verify scripts for Phase 7.3-7.10 hubs."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

HUBS = [
    ("7.3", "ai_copilot", "ai-copilot", "AI Copilot", "AI_COPILOT_REPORT.json", 11,
     ["/ai-clinical", "/api/v1/ai-operations/dashboard"]),
    ("7.4", "mobile_platform", "mobile-platform", "Mobile Platform", "MOBILE_PLATFORM_REPORT.json", 8,
     ["/api/v1/collector/jobs", ("/api/v1/auth/refresh", "POST")]),
    ("7.5", "device_gateway", "device-gateway", "Device Gateway", "DEVICE_GATEWAY_REPORT.json", 10,
     ["/iot-logistics", "/api/v1/integration-hub/dashboard"]),
    ("7.6", "voice_platform", "voice-platform", "Voice Platform", "VOICE_PLATFORM_REPORT.json", 6, []),
    ("7.7", "data_warehouse", "data-warehouse", "Data Warehouse", "DATA_WAREHOUSE_REPORT.json", 6,
     ["/api/v1/reports", "/api/v1/enterprise-analytics/dashboard"]),
    ("7.8", "population_health", "population-health", "Population Health", "POPULATION_HEALTH_REPORT.json", 9,
     ["/api/v1/diseases"]),
    ("7.9", "white_label", "white-label", "White Label", "WHITE_LABEL_REPORT.json", 7,
     ["/api/v1/multi-tenant/settings"]),
    ("7.10", "federation_platform", "federation-platform", "Federation Platform", "FEDERATION_PLATFORM_REPORT.json", 7,
     ["/api/v1/federation/labs", "/federation"]),
]

TEMPLATE = '''#!/usr/bin/env python3
"""Verify {title} Phase {phase}."""

from __future__ import annotations

import json, os, sys, time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = ROOT / "generated_release" / "{report}"

WEB_ROUTES = {web_routes}
API_ROUTES = {api_routes}


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
    payload = response.get_json() or {{}}
    if isinstance(payload, dict) and payload.get("success") is True and "data" in payload:
        return payload["data"]
    return payload


def main() -> int:
    sys.path.insert(0, str(ROOT))
    if not os.getenv("DATABASE_URL"):
        print("FAIL: DATABASE_URL required", file=sys.stderr)
        return 1
    print("\\n=== DXCON {title_upper} VERIFY ===\\n")
    start = time.perf_counter()
    checks = {{}}
    from app import create_app
    app = create_app()
    with app.app_context():
        from app.core.passwords import hash_password
        from app.extensions.db import db
        from app.models.user import User
        from app.services.{slug}_service import FEATURES, {ensure_fn}
        db.create_all()
        if not User.query.filter(User.role.in_(("SUPER_ADMIN", "ADMIN"))).first():
            db.session.add(User(email="verify-{slug}@demo.dxcon.test", role="ADMIN", password_hash=hash_password("DemoPass123!"), is_active=True))
            db.session.commit()
        {ensure_fn}()
        routes = {{str(r.rule) for r in app.url_map.iter_rules()}}
        missing_web = [r for r in WEB_ROUTES if r not in routes]
        missing_api = [r for r in API_ROUTES if r not in routes]
        checks["route_registry"] = {{"ok": not missing_web and not missing_api, "missing_web": missing_web, "missing_api": missing_api}}
        client = app.test_client()
        checks["auth"] = {{"ok": _login_admin(client)}}
        web_ok = all((client.get(r, follow_redirects=True).status_code == 200) for r in WEB_ROUTES)
        checks["web_pages"] = {{"ok": web_ok}}
        api_ok = all((client.get(r, follow_redirects=True).status_code == 200) for r in API_ROUTES)
        checks["api_endpoints"] = {{"ok": api_ok}}
        dash = _api_json(client.get("/api/v1/{prefix}/dashboard"))
        checks["feature_coverage"] = {{"ok": len(dash.get("features", [])) == {feature_count} and list(FEATURES) == dash.get("features")}}
{legacy_checks}
    passed = sum(1 for c in checks.values() if c.get("ok"))
    total = len(checks)
    score = round((passed / total) * 100, 1) if total else 0
    report = {{"generated_at": utc_now(), "phase": "{phase}", "sprint": "{title}", "summary": {{"score": score, "checks_passed": passed, "checks_total": total, "ok": passed == total, "runtime_seconds": round(time.perf_counter() - start, 3)}}, "checks": checks}}
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    print(f"{title} score: {{score}}% ({{passed}}/{{total}})")
    print("PASS\\n" if report["summary"]["ok"] else "FAIL\\n")
    return 0 if report["summary"]["ok"] else 1

if __name__ == "__main__":
    raise SystemExit(main())
'''


def _routes_from_file(path: Path, marker: str = '.route("') -> list[str]:
    routes: list[str] = []
    for line in path.read_text().splitlines():
        if marker in line:
            routes.append(line.split(marker)[1].split('"')[0])
    return list(dict.fromkeys(routes))


def main():
    ensure_map = {
        "ai_copilot": "ensure_ai_copilot",
        "mobile_platform": "ensure_mobile_platform",
        "device_gateway": "ensure_device_gateway",
        "voice_platform": "ensure_voice_platform",
        "data_warehouse": "ensure_data_warehouse",
        "population_health": "ensure_population_health",
        "white_label": "ensure_white_label",
        "federation_platform": "ensure_federation_platform",
    }
    for phase, slug, prefix, title, report, feature_count, legacy in HUBS:
        web_path = ROOT / "app" / "web" / f"{slug}.py"
        api_path = ROOT / "app" / "api" / slug / "routes.py"
        web_routes = _routes_from_file(web_path)
        api_routes = [f"/api/v1/{prefix}{route}" for route in _routes_from_file(api_path)]

        ensure_fn = ensure_map[slug]
        legacy_checks = ""
        for i, leg in enumerate(legacy):
            key = f"legacy_{i}"
            if isinstance(leg, tuple):
                path, method = leg[0], leg[1]
                if method == "POST":
                    legacy_checks += (
                        f'        checks["{key}"] = {{"ok": "{path}" in routes and '
                        f'client.post("{path}", json={{}}).status_code != 404}}\n'
                    )
                else:
                    legacy_checks += f'        checks["{key}"] = {{"ok": client.get("{path}", follow_redirects=True).status_code == 200}}\n'
            else:
                legacy_checks += f'        checks["{key}"] = {{"ok": client.get("{leg}", follow_redirects=True).status_code == 200}}\n'

        content = TEMPLATE.format(
            phase=phase,
            slug=slug,
            prefix=prefix,
            title=title,
            title_upper=title.upper(),
            report=report,
            feature_count=feature_count,
            web_routes=tuple(web_routes),
            api_routes=tuple(api_routes),
            ensure_fn=ensure_fn,
            legacy_checks=legacy_checks,
        )
        out = ROOT / "scripts" / f"verify_{slug}.py"
        out.write_text(content, encoding="utf-8")
        print("wrote", out.name)


if __name__ == "__main__":
    main()
