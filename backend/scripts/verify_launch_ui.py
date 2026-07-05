#!/usr/bin/env python3
"""Verify Launch UI routes, styling, and Sprint 2 functional navigation."""

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
SPRINT2_REPORT_PATH = GENERATED / "LAUNCH_UI_SPRINT2_REPORT.json"
SPRINT3_REPORT_PATH = GENERATED / "LAUNCH_UI_SPRINT3_REPORT.json"

PUBLIC_ROUTES = (
    "/home",
    "/login",
    "/health",
    "/ready",
)

ROLE_DASHBOARD_ROUTES = (
    "/app/executive",
    "/app/reception",
    "/app/doctor",
    "/app/lab",
    "/app/collector",
    "/app/patient",
    "/app/system",
    "/executive-v10",
)

STYLED_ROUTES = (
    "/login",
    "/home",
    *ROLE_DASHBOARD_ROUTES,
)

CSS_MARKER = "css/dxcon.css"

ROLE_DEMO_CHECKS = (
    ("ADMIN", "/app/executive"),
    ("DOCTOR", "/app/doctor"),
    ("LAB", "/app/lab"),
    ("RECEPTION", "/app/reception"),
    ("COLLECTOR", "/app/collector"),
    ("PATIENT", "/app/patient"),
)


def _routes_from_file(path: Path) -> list[str]:
    routes: list[str] = []
    for line in path.read_text().splitlines():
        if '.route("' in line:
            routes.append(line.split('.route("')[1].split('"')[0])
    return list(dict.fromkeys(routes))


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _login_admin(client):
    from app.models.user import User

    user = User.query.filter(User.role == "SUPER_ADMIN").first() or User.query.filter(User.role == "ADMIN").first()
    if not user:
        return False
    with client.session_transaction() as sess:
        sess.clear()
        sess["user_id"] = user.id
        sess["role"] = user.role
        sess["email"] = user.email
    return True


def _has_stylesheet(html_text: str) -> bool:
    return CSS_MARKER in (html_text or "")


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

    from app.web.launch_ui_modules import MODULE_ROUTES

    print("\n=== DXCON LAUNCH UI VERIFY ===\n")
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

        dashboard_routes = _routes_from_file(ROOT / "app" / "web" / "launch_ui.py")
        routes = {str(r.rule) for r in app.url_map.iter_rules()}
        missing_dashboard = [r for r in dashboard_routes if r not in routes]
        missing_modules = [r for r in MODULE_ROUTES if r not in routes]
        checks["route_registry"] = {
            "ok": not missing_dashboard and not missing_modules,
            "missing_dashboard": missing_dashboard,
            "missing_modules": missing_modules,
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
        for path in ROLE_DASHBOARD_ROUTES:
            response = client.get(path, follow_redirects=True)
            body = response.get_data(as_text=True) or ""
            app_results[path] = {
                "status_code": response.status_code,
                "ok": response.status_code == 200 and "launch-shell" in body and _has_stylesheet(body),
            }
        checks["role_dashboards"] = {
            "ok": all(item["ok"] for item in app_results.values()),
            "routes": app_results,
        }

        module_results = {}
        for path in MODULE_ROUTES:
            response = client.get(path, follow_redirects=True)
            body = response.get_data(as_text=True) or ""
            module_results[path] = {
                "status_code": response.status_code,
                "ok": response.status_code == 200 and "launch-shell" in body and _has_stylesheet(body),
            }
        checks["module_pages"] = {
            "ok": all(item["ok"] for item in module_results.values()),
            "routes": module_results,
        }

        login_html = client.get("/login").get_data(as_text=True)
        checks["login_shell"] = {
            "ok": "launch-login-card" in login_html and "Sign in" in login_html and _has_stylesheet(login_html),
        }
        home_html = client.get("/home").get_data(as_text=True)
        checks["marketing_shell"] = {
            "ok": "launch-marketing-hero" in home_html and _has_stylesheet(home_html),
        }

        css_response = client.get("/static/css/dxcon.css")
        css_text = css_response.get_data(as_text=True)
        checks["static_css_asset"] = {
            "ok": css_response.status_code == 200 and ".launch-action-card" in css_text,
            "status_code": css_response.status_code,
        }

        styled_results = {}
        for path in STYLED_ROUTES:
            if path == "/login":
                page_html = login_html
            elif path == "/home":
                page_html = home_html
            else:
                page_html = client.get(path, follow_redirects=True).get_data(as_text=True)
            styled_results[path] = {"ok": _has_stylesheet(page_html)}
        checks["stylesheet_links"] = {
            "ok": all(item["ok"] for item in styled_results.values()),
            "routes": styled_results,
        }

        demo_results = {}
        for role, target in ROLE_DEMO_CHECKS:
            with client.session_transaction() as sess:
                sess.clear()
            response = client.get(f"/login/demo?role={role}", follow_redirects=False)
            location = response.headers.get("Location") or ""
            demo_results[role] = {
                "ok": response.status_code in {302, 303, 307, 308} and target in location,
                "location": location,
            }
        checks["demo_role_entry"] = {
            "ok": all(item["ok"] for item in demo_results.values()),
            "routes": demo_results,
        }

        demo_exec = client.get("/login/demo?role=ADMIN", follow_redirects=True)
        checks["demo_dashboard_entry"] = {
            "ok": demo_exec.status_code == 200 and "/app/executive" in (demo_exec.request.path or ""),
        }

        from app.web.launch_ui_data import get_demo_counts, get_sample_order_key, get_sample_patient_key, get_sample_report_key

        counts = get_demo_counts()
        checks["demo_data_layer"] = {
            "ok": all(k in counts for k in ("patients", "orders", "tests", "revenue", "pending_reports")),
            "counts": counts,
        }

        detail_routes = {
            "patient": f"/app/patients/{get_sample_patient_key()}",
            "order": f"/app/orders/{get_sample_order_key()}",
            "report": f"/app/reports/{get_sample_report_key()}",
        }
        detail_results = {}
        page_markers = {
            "/app/executive": "Recent orders",
            "/app/patients": "Patient directory",
            "/app/orders": "Recent orders",
            "/app/reports": "Report queue",
            "/app/finance": "Invoices",
            "/app/ai": "Safety disclaimer",
            "/app/samples": "Sample queue",
            "/app/iot": "Cold boxes",
            detail_routes["patient"]: "Orders timeline",
            detail_routes["order"]: "Order timeline",
            detail_routes["report"]: "Report preview",
        }
        marker_results = {}
        for path, marker in page_markers.items():
            response = client.get(path, follow_redirects=True)
            body = response.get_data(as_text=True) or ""
            marker_results[path] = {
                "ok": response.status_code == 200 and marker in body and _has_stylesheet(body),
                "status_code": response.status_code,
                "marker": marker,
            }
        for name, path in detail_routes.items():
            response = client.get(path, follow_redirects=True)
            body = response.get_data(as_text=True) or ""
            detail_results[path] = {
                "ok": response.status_code == 200 and "launch-shell" in body,
                "status_code": response.status_code,
            }
        checks["detail_routes"] = {
            "ok": all(item["ok"] for item in detail_results.values()),
            "routes": detail_results,
        }
        checks["page_markers"] = {
            "ok": all(item["ok"] for item in marker_results.values()),
            "routes": marker_results,
        }

        no_500_paths = list(MODULE_ROUTES) + list(ROLE_DASHBOARD_ROUTES) + list(detail_routes.values())
        status_results = {path: client.get(path, follow_redirects=True).status_code for path in no_500_paths}
        checks["no_server_errors"] = {
            "ok": all(code == 200 for code in status_results.values()),
            "status_codes": status_results,
        }

        passed = sum(1 for item in checks.values() if item.get("ok"))
        total = len(checks)
        elapsed = round(time.perf_counter() - start, 2)

        summary = {"passed": passed, "total": total, "ok": passed == total}
        route_payload = {
            "public": list(PUBLIC_ROUTES),
            "role_dashboards": list(ROLE_DASHBOARD_ROUTES),
            "modules": list(MODULE_ROUTES),
            "detail": detail_routes,
            "demo_entry": [{"role": r, "target": t} for r, t in ROLE_DEMO_CHECKS],
        }

        report = {
            "sprint": "Launch UI Sprint 3",
            "generated_at": utc_now(),
            "elapsed_seconds": elapsed,
            "checks": checks,
            "routes": route_payload,
            "demo_counts": counts,
            "summary": summary,
        }

        sprint2_report = {
            **report,
            "sprint": "Launch UI Sprint 2 - Functional Role Navigation",
            "module_route_count": len(MODULE_ROUTES),
        }
        sprint3_report = {
            **report,
            "sprint": "Launch UI Sprint 3 - Real Demo Data and Workflow Pages",
            "detail_route_count": len(detail_routes),
        }

        GENERATED.mkdir(parents=True, exist_ok=True)
        REPORT_PATH.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
        SPRINT2_REPORT_PATH.write_text(json.dumps(sprint2_report, indent=2, default=str), encoding="utf-8")
        SPRINT3_REPORT_PATH.write_text(json.dumps(sprint3_report, indent=2, default=str), encoding="utf-8")

        for name, payload in checks.items():
            print(f"{'PASS' if payload.get('ok') else 'FAIL'}: {name}")
            if not payload.get("ok"):
                for key, value in payload.items():
                    if key != "ok" and value:
                        print(f"  {key}: {value}")

        print(f"\nSummary: {passed}/{total} passed in {elapsed}s")
        print(f"Report: {REPORT_PATH}")
        print(f"Sprint 2 report: {SPRINT2_REPORT_PATH}")
        print(f"Sprint 3 report: {SPRINT3_REPORT_PATH}\n")
        return 0 if summary["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
