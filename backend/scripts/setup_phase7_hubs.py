#!/usr/bin/env python3
"""Generate Phase 7.3-7.10 hub web/api/verify/test scaffolding."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

HUBS = [
    {
        "phase": "7.3",
        "slug": "ai_copilot",
        "prefix": "ai-copilot",
        "title": "AI Copilot Platform",
        "roles": "AI_COPILOT_ROLES",
        "service": "ai_copilot_service",
        "features": [
            ("reception-copilot", "reception_copilot", "Reception Copilot"),
            ("doctor-copilot", "doctor_copilot", "Doctor Copilot"),
            ("collector-copilot", "collector_copilot", "Collector Copilot"),
            ("lab-copilot", "lab_copilot", "Lab Copilot"),
            ("ceo-copilot", "ceo_copilot", "CEO Copilot"),
            ("prompts", "prompt_registry_view", "Prompt Registry"),
            ("prompt-versions", "prompt_version_view", "Prompt Version"),
            ("audit", "conversation_audit", "Conversation Audit"),
            ("safety", "safety_layer", "Safety Layer"),
            ("phi-redaction", "phi_redaction_demo", "PHI Redaction"),
            ("routing", "ai_routing", "AI Routing"),
        ],
        "commit": "Phase 7.3 AI Copilot",
        "report": "AI_COPILOT_REPORT.json",
    },
    {
        "phase": "7.4",
        "slug": "mobile_platform",
        "prefix": "mobile-platform",
        "title": "Mobile Platform",
        "roles": "MOBILE_PLATFORM_ROLES",
        "service": "mobile_platform_service",
        "features": [
            ("collector-api", "collector_api", "Collector API"),
            ("doctor-api", "doctor_api", "Doctor API"),
            ("patient-api", "patient_api", "Patient API"),
            ("notifications", "notification_api", "Notification API"),
            ("offline-sync", "offline_sync_api", "Offline Sync API"),
            ("token-refresh", "token_refresh", "Token Refresh"),
            ("conflict-resolution", "conflict_resolution", "Conflict Resolution"),
            ("pwa-manifest", "pwa_manifest", "PWA Manifest"),
        ],
        "commit": "Phase 7.4 Mobile Platform",
        "report": "MOBILE_PLATFORM_REPORT.json",
    },
    {
        "phase": "7.5",
        "slug": "device_gateway",
        "prefix": "device-gateway",
        "title": "Device Gateway",
        "roles": "DEVICE_GATEWAY_ROLES",
        "service": "device_gateway_service",
        "features": [
            ("registry", "gateway_registry", "Gateway Registry"),
            ("astm", "astm_adapter", "ASTM Adapter"),
            ("hl7", "hl7_adapter", "HL7 Adapter"),
            ("tcp", "tcp_adapter", "TCP Adapter"),
            ("serial", "serial_adapter", "Serial Adapter"),
            ("usb", "usb_adapter", "USB Adapter"),
            ("simulator", "device_simulator", "Simulator"),
            ("device-queue", "device_queue", "Device Queue"),
            ("retry-queue", "retry_queue", "Retry Queue"),
            ("audit", "device_audit", "Device Audit"),
        ],
        "commit": "Phase 7.5 Device Gateway",
        "report": "DEVICE_GATEWAY_REPORT.json",
    },
    {
        "phase": "7.6",
        "slug": "voice_platform",
        "prefix": "voice-platform",
        "title": "Voice Platform",
        "roles": "VOICE_PLATFORM_ROLES",
        "service": "voice_platform_service",
        "features": [
            ("speech-api", "speech_api", "Speech API"),
            ("transcripts", "transcript_storage", "Transcript Storage"),
            ("clinical-notes", "clinical_note_generator", "Clinical Note Generator"),
            ("ai-summary", "ai_summary", "AI Summary"),
            ("sessions", "voice_session", "Voice Session"),
            ("audit", "voice_audit", "Voice Audit"),
        ],
        "commit": "Phase 7.6 Voice Platform",
        "report": "VOICE_PLATFORM_REPORT.json",
    },
    {
        "phase": "7.7",
        "slug": "data_warehouse",
        "prefix": "data-warehouse",
        "title": "Data Warehouse",
        "roles": "DATA_WAREHOUSE_ROLES",
        "service": "data_warehouse_service",
        "features": [
            ("etl", "etl_layer", "ETL Layer"),
            ("facts", "fact_tables", "Fact Tables"),
            ("dimensions", "dimension_tables", "Dimension Tables"),
            ("analytics", "analytics_api", "Analytics API"),
            ("bi-export", "bi_export", "BI Export"),
            ("powerbi", "powerbi_export", "PowerBI Export"),
        ],
        "commit": "Phase 7.7 Data Warehouse",
        "report": "DATA_WAREHOUSE_REPORT.json",
    },
    {
        "phase": "7.8",
        "slug": "population_health",
        "prefix": "population-health",
        "title": "Population Health",
        "roles": "POPULATION_HEALTH_ROLES",
        "service": "population_health_service",
        "features": [
            ("registry", "disease_registry", "Disease Registry"),
            ("dashboard", "population_dashboard", "Population Dashboard"),
            ("risk-groups", "risk_groups", "Risk Groups"),
            ("vaccination", "vaccination_statistics", "Vaccination Statistics"),
            ("diabetes", "diabetes_panel", "Diabetes"),
            ("hypertension", "hypertension_panel", "Hypertension"),
            ("cancer", "cancer_panel", "Cancer"),
            ("womens-health", "womens_health_panel", "Women's Health"),
            ("children", "children_panel", "Children"),
        ],
        "commit": "Phase 7.8 Population Health",
        "report": "POPULATION_HEALTH_REPORT.json",
    },
    {
        "phase": "7.9",
        "slug": "white_label",
        "prefix": "white-label",
        "title": "White Label",
        "roles": "WHITE_LABEL_ROLES",
        "service": "white_label_service",
        "features": [
            ("theme", "brand_theme", "Brand Theme"),
            ("logo", "brand_logo", "Logo"),
            ("email", "email_template", "Email Template"),
            ("sms", "sms_template", "SMS Template"),
            ("domain", "tenant_domain", "Tenant Domain"),
            ("branding", "tenant_branding", "Tenant Branding"),
            ("config", "tenant_config", "Tenant Config"),
        ],
        "commit": "Phase 7.9 White Label",
        "report": "WHITE_LABEL_REPORT.json",
    },
    {
        "phase": "7.10",
        "slug": "federation_platform",
        "prefix": "federation-platform",
        "title": "Federation Platform",
        "roles": "FEDERATION_PLATFORM_ROLES",
        "service": "federation_platform_service",
        "features": [
            ("regional", "regional_hub", "Regional Hub"),
            ("national", "national_hub", "National Hub"),
            ("clinic-federation", "clinic_federation", "Clinic Federation"),
            ("lab-federation", "laboratory_federation", "Laboratory Federation"),
            ("exchange", "cross_organization_exchange", "Cross Organization Exchange"),
            ("sync-queue", "sync_queue", "Sync Queue"),
            ("audit", "federation_audit", "Federation Audit"),
        ],
        "commit": "Phase 7.10 Federation",
        "report": "FEDERATION_PLATFORM_REPORT.json",
    },
]


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
    nav = ",\n    ".join(
        f'("{label}", "/{prefix}"' + ("" if i == 0 else f'/{route}"') + ")"
        for i, (route, _, label) in enumerate(hub["features"])
    )
    if hub["features"]:
        nav = f'("Overview", "/{prefix}"),\n    ' + ",\n    ".join(
            f'("{label}", "/{prefix}/{route}")' for route, _, label in hub["features"]
        )
    builds = "\n".join(
        f"def build_{fn}_body() -> str:\n    return build_json_section({label!r}, svc.{fn}())\n"
        for _, fn, label in hub["features"]
    )
    imports = ",\n    ".join(f"build_{fn}_body" for _, fn, _ in hub["features"])
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
    <body><div class="wrap"><div class="nav">{{nav}}</div><div class="muted-note">{hub["title"]} · Phase {hub["phase"]}</div>{{body_html}}</div></body>
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
    return f"""
    {{page_header("{hub["title"]}", "Phase {hub["phase"]} enterprise hub.")}}
    {{cards}}
    <div class="card"><h3>Features</h3><ul>{{features}}</ul></div>
    """


{builds}
'''
    path = ROOT / "app" / "web" / f"{slug}_lib.py"
    path.write_text(content, encoding="utf-8")


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

class {slug.title().replace("_", "")}TestCase(unittest.TestCase):
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
        self.assertEqual(d.get_json()["phase"], "{hub["phase"]}")
'''
    (ROOT / "tests" / f"test_{slug}_hub.py").write_text(content, encoding="utf-8")


def main():
    for hub in HUBS:
        if hub["slug"] == "ai_copilot":
            write_api(hub)
            write_web_lib(hub)
            write_web(hub)
            write_test(hub)
            continue
        write_api(hub)
        write_web_lib(hub)
        write_web(hub)
        write_test(hub)
        print("scaffolded", hub["slug"])


if __name__ == "__main__":
    main()
