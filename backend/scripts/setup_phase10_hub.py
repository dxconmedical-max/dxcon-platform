#!/usr/bin/env python3
"""Generate Phase 10 Healthcare Ecosystem hub scaffolding."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

HUB = {
    "phase": "10",
    "slug": "healthcare_ecosystem",
    "prefix": "healthcare-ecosystem",
    "title": "Healthcare Ecosystem",
    "roles": "HEALTHCARE_ECOSYSTEM_ROLES",
    "service": "healthcare_ecosystem_service",
    "subtitle": "DxCon Enterprise v1.0 commercial release ecosystem",
    "features": [
        ("dxcon-lab", "dxcon_lab", "DxCon Lab"),
        ("dxcon-clinic", "dxcon_clinic", "DxCon Clinic"),
        ("dxcon-home", "dxcon_home", "DxCon Home"),
        ("dxcon-pharmacy", "dxcon_pharmacy", "DxCon Pharmacy"),
        ("dxcon-insurance", "dxcon_insurance", "DxCon Insurance"),
        ("dxcon-ai", "dxcon_ai", "DxCon AI"),
        ("dxcon-cloud", "dxcon_cloud", "DxCon Cloud"),
        ("dxcon-marketplace", "dxcon_marketplace", "DxCon Marketplace"),
        ("partner-portal", "partner_portal", "Partner Portal"),
        ("customer-portal", "customer_portal", "Customer Portal"),
        ("enterprise-governance", "enterprise_governance", "Enterprise Governance"),
        ("architecture-board", "architecture_board", "Architecture Board"),
        ("release-board", "release_board", "Release Board"),
        ("medical-governance", "medical_governance", "Medical Governance"),
        ("security-governance", "security_governance", "Security Governance"),
        ("ai-governance", "ai_governance", "AI Governance"),
        ("enterprise-audit", "enterprise_audit", "Enterprise Audit"),
        ("customer-success", "customer_success_portal", "Customer Success Portal"),
        ("training-center", "training_center", "Training Center"),
        ("certification-center", "certification_center", "Certification Center"),
        ("release-manager", "release_manager", "Release Manager"),
        ("license-manager", "license_manager", "License Manager"),
        ("commercial-readiness", "commercial_readiness", "Commercial Readiness"),
        ("support-center", "support_center", "Support Center"),
        ("knowledge-base", "knowledge_base", "Knowledge Base"),
    ],
}


def write_api(hub: dict) -> None:
    slug = hub["slug"]
    prefix = hub["prefix"]
    svc = hub["service"]
    lines = [
        f'"""{hub["title"]} API routes — Phase {hub["phase"]}."""',
        "",
        "from __future__ import annotations",
        "",
        "from flask import Blueprint",
        "",
        f"from app.services.{svc} import (",
        "    dashboard_payload,",
    ]
    for _, fn, _ in hub["features"]:
        lines.append(f"    {fn},")
    lines.append(f"    {slug}_readiness_report,")
    lines.append(")")
    lines.append("")
    lines.append(f'{slug}_bp = Blueprint("{slug}_api", __name__, url_prefix="/api/v1/{prefix}")')
    lines.append("")
    lines.append(f'@{slug}_bp.route("/dashboard", methods=["GET"])')
    lines.append(f"def {slug}_dashboard_api():")
    lines.append("    return dashboard_payload()")
    lines.append("")
    for route, fn, _ in hub["features"]:
        lines.append(f'@{slug}_bp.route("/{route}", methods=["GET"])')
        lines.append(f"def {slug}_{fn}_api():")
        lines.append(f"    return {fn}()")
        lines.append("")
    lines.append(f'@{slug}_bp.route("/readiness", methods=["GET"])')
    lines.append(f"def {slug}_readiness_api():")
    lines.append(f"    return {slug}_readiness_report()")
    lines.append("")
    path = ROOT / "app" / "api" / slug / "routes.py"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def write_web_lib(hub: dict) -> None:
    slug = hub["slug"]
    prefix = hub["prefix"]
    svc = hub["service"]
    nav = f'("Overview", "/{prefix}"),\n    ' + ",\n    ".join(
        f'("{label}", "/{prefix}/{route}")' for route, _, label in hub["features"]
    )
    builds = "\n".join(
        f"def build_{fn}_body() -> str:\n    return build_json_section({label!r}, svc.{fn}())\n"
        for _, fn, label in hub["features"]
    )
    imports = ",\n    ".join(f"build_{fn}_body" for _, fn, _ in hub["features"])
    feature_count = len(hub["features"])
    content = f'''"""{hub["title"]} web rendering helpers — Phase {hub["phase"]}."""

from __future__ import annotations

import html
import json

from app.services import {svc} as svc
from app.web.demo_pilot_lib import metric_cards, page_header, pilot_styles

NAV = (
    {nav}
)


def hub_styles() -> str:
    return pilot_styles() + """
    pre {{ background:#0f172a; color:#e2e8f0; padding:12px; border-radius:8px; overflow:auto; white-space:pre-wrap; font-size:13px; }}
    .muted-note {{ color:#64748b; font-size:13px; margin-bottom:16px; }}
    """


def render_hub_page(title: str, body_html: str) -> str:
    nav = "".join(f'<a href="{{href}}">{{label}}</a>' for label, href in NAV)
    return f"""
    <html>
    <head><title>{{title}}</title><meta name="viewport" content="width=device-width, initial-scale=1" /><style>{{hub_styles()}}</style></head>
    <body><div class="wrap"><div class="nav">{{nav}}</div><div class="muted-note">{hub["title"]} · Phase {hub["phase"]} · {hub["subtitle"]}</div>{{body_html}}</div></body>
    </html>
    """


def build_json_section(title: str, data: dict) -> str:
    return f"""
    {{page_header(title, data.get("report", ""))}}
    <div class="card"><pre>{{html.escape(json.dumps(data, indent=2, default=str))}}</pre></div>
    """


def build_dashboard_body() -> str:
    data = svc.dashboard_payload()
    summary = data.get("summary", {{}})
    cards = metric_cards([(k.replace("_", " ").title(), v) for k, v in list(summary.items())[:6]])
    features = "".join(f"<li>{{html.escape(item)}}</li>" for item in data.get("features", []))
    release = data.get("release", {{}})
    release_html = "".join(f"<li>{{html.escape(k)}}: {{html.escape(str(v))}}</li>" for k, v in release.items())
    return f"""
    {{page_header("{hub["title"]}", "Phase {hub["phase"]} — {hub["subtitle"]}.")}}
    {{cards}}
    <div class="card"><h3>Release</h3><ul>{{release_html}}</ul></div>
    <div class="card"><h3>Ecosystem ({feature_count})</h3><ul>{{features}}</ul></div>
    """


{builds}
'''
    (ROOT / "app" / "web" / f"{slug}_lib.py").write_text(content, encoding="utf-8")


def write_web(hub: dict) -> None:
    slug = hub["slug"]
    prefix = hub["prefix"]
    roles = hub["roles"]
    imports = ",\n    ".join(f"build_{fn}_body" for _, fn, _ in hub["features"])
    routes = [
        f'@{slug}_web_bp.route("/{prefix}")\n@role_required(*{roles})\ndef {slug}_dashboard():\n    return render_hub_page("{hub["title"]}", build_dashboard_body())\n'
    ]
    for route, fn, label in hub["features"]:
        routes.append(
            f'@{slug}_web_bp.route("/{prefix}/{route}")\n@role_required(*{roles})\ndef {slug}_{fn}():\n    return render_hub_page("{label}", build_{fn}_body())\n'
        )
    content = f'''"""{hub["title"]} web routes — Phase {hub["phase"]}."""

from __future__ import annotations

from flask import Blueprint

from app.services.{hub["service"]} import {roles}
from app.utils.auth import role_required
from app.web.{slug}_lib import (
    build_dashboard_body,
    {imports},
    render_hub_page,
)

{slug}_web_bp = Blueprint("{slug}_web", __name__)

{"".join(routes)}
'''
    (ROOT / "app" / "web" / f"{slug}.py").write_text(content, encoding="utf-8")


def write_test(hub: dict) -> None:
    slug = hub["slug"]
    prefix = hub["prefix"]
    content = f'''import os, sys, unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

class HealthcareEcosystemTestCase(unittest.TestCase):
    def setUp(self):
        from app import create_app
        from app.core.passwords import hash_password
        from app.extensions.db import db
        from app.models.user import User
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()
        self.client = self.app.test_client()
        user = User(email="demo-{slug}@demo.dxcon.test", role="ADMIN", password_hash=hash_password("DemoPass123!"), is_active=True)
        db.session.add(user)
        db.session.commit()
        with self.client.session_transaction() as sess:
            sess["user_id"] = user.id
            sess["role"] = user.role
            sess["email"] = user.email

    def tearDown(self):
        from app.extensions.db import db
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def test_routes_registered(self):
        routes = {{str(r.rule) for r in self.app.url_map.iter_rules()}}
        self.assertIn("/{prefix}", routes)
        self.assertIn("/api/v1/{prefix}/dashboard", routes)

    def test_dashboard(self):
        r = self.client.get("/{prefix}")
        self.assertEqual(r.status_code, 200)
        d = self.client.get("/api/v1/{prefix}/dashboard")
        self.assertEqual(d.status_code, 200)
        payload = d.get_json()
        if isinstance(payload, dict) and payload.get("success"):
            payload = payload["data"]
        self.assertEqual(payload["phase"], "{hub["phase"]}")
        self.assertEqual(payload["release"]["tag"], "v1.0.0-rc1")

    def test_ecosystem_modules(self):
        from app.services.{hub["service"]} import FEATURES, RELEASE
        self.assertEqual(len(FEATURES), {len(hub["features"])})
        self.assertEqual(RELEASE["version"], "1.0.0-rc1")
'''
    (ROOT / "tests" / f"test_{slug}_hub.py").write_text(content, encoding="utf-8")


def main():
    write_api(HUB)
    write_web_lib(HUB)
    write_web(HUB)
    write_test(HUB)
    print("scaffolded", HUB["slug"], f"({len(HUB['features'])} features)")


if __name__ == "__main__":
    main()
