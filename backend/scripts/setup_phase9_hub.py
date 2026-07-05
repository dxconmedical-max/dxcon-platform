#!/usr/bin/env python3
"""Generate Phase 9 Regional Cloud Platform hub scaffolding."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

HUB = {
    "phase": "9",
    "slug": "regional_cloud",
    "prefix": "regional-cloud",
    "title": "Regional Cloud Platform",
    "roles": "REGIONAL_CLOUD_ROLES",
    "service": "regional_cloud_service",
    "subtitle": "Multi-country deployment with regional compliance and cloud abstraction",
    "features": [
        ("regional-deployment", "regional_deployment", "Regional Deployment"),
        ("localization", "localization", "Localization"),
        ("internationalization", "internationalization", "Internationalization"),
        ("language-packs", "language_packs", "Language Packs"),
        ("currency-engine", "currency_engine", "Currency Engine"),
        ("tax-engine", "tax_engine", "Tax Engine"),
        ("timezone-engine", "timezone_engine", "Timezone Engine"),
        ("holiday-engine", "holiday_engine", "Holiday Engine"),
        ("regional-compliance", "regional_compliance", "Regional Compliance"),
        ("hipaa", "hipaa_compliance", "HIPAA"),
        ("gdpr", "gdpr_compliance", "GDPR"),
        ("pdpa", "pdpa_compliance", "PDPA"),
        ("iso27001", "iso27001_preparation", "ISO27001"),
        ("soc2", "soc2_preparation", "SOC2 Preparation"),
        ("geo-replication", "geo_replication", "Geo Replication"),
        ("cross-region-federation", "cross_region_federation", "Cross-region Federation"),
        ("regional-marketplace", "regional_marketplace", "Regional Marketplace"),
        ("regional-partner-portal", "regional_partner_portal", "Regional Partner Portal"),
        ("cloud-abstraction", "cloud_abstraction_layer", "Cloud Abstraction Layer"),
        ("aws", "aws_provider", "AWS"),
        ("azure", "azure_provider", "Azure"),
        ("google-cloud", "google_cloud_provider", "Google Cloud"),
        ("render", "render_provider", "Render"),
        ("on-premise", "on_premise_provider", "On-premise"),
        ("multi-region-backup", "multi_region_backup", "Multi-region Backup"),
        ("disaster-recovery", "disaster_recovery", "Disaster Recovery"),
        ("regional-monitoring", "regional_monitoring", "Regional Monitoring"),
        ("regional-analytics", "regional_analytics", "Regional Analytics"),
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
    policy = data.get("governance", {{}})
    policy_html = "".join(f"<li>{{html.escape(k)}}: {{html.escape(str(v))}}</li>" for k, v in policy.items())
    return f"""
    {{page_header("{hub["title"]}", "Phase {hub["phase"]} — {hub["subtitle"]}.")}}
    {{cards}}
    <div class="card"><h3>Governance</h3><ul>{{policy_html}}</ul></div>
    <div class="card"><h3>Modules ({feature_count})</h3><ul>{{features}}</ul></div>
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

class RegionalCloudTestCase(unittest.TestCase):
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
        self.assertTrue(payload.get("governance", {{}}).get("backward_compatible"))

    def test_governance(self):
        from app.services.{hub["service"]} import FEATURES, GOVERNANCE
        self.assertEqual(len(FEATURES), {len(hub["features"])})
        self.assertTrue(GOVERNANCE["postgresql_only"])
        self.assertFalse(GOVERNANCE["destructive_migrations"])
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
