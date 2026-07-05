"""Federation Platform web rendering helpers — Phase 7.10."""

from __future__ import annotations

import html
import json

from app.services import federation_platform_service as svc
from app.web.demo_pilot_lib import metric_cards, page_header, pilot_styles

NAV = (
    ("Overview", "/federation-platform"),
    ("Regional Hub", "/federation-platform/regional"),
    ("National Hub", "/federation-platform/national"),
    ("Clinic Federation", "/federation-platform/clinic-federation"),
    ("Laboratory Federation", "/federation-platform/lab-federation"),
    ("Cross Organization Exchange", "/federation-platform/exchange"),
    ("Sync Queue", "/federation-platform/sync-queue"),
    ("Federation Audit", "/federation-platform/audit")
)


def hub_styles() -> str:
    return pilot_styles() + """
    pre { background:#0f172a; color:#e2e8f0; padding:12px; border-radius:8px; overflow:auto; white-space:pre-wrap; font-size:13px; }
    .muted-note { color:#64748b; font-size:13px; margin-bottom:16px; }
    """


def render_hub_page(title: str, body_html: str) -> str:
    nav = "".join(f'<a href="{href}">{label}</a>' for label, href in NAV)
    return f"""
    <html>
    <head><title>{title}</title><meta name="viewport" content="width=device-width, initial-scale=1" /><style>{hub_styles()}</style></head>
    <body><div class="wrap"><div class="nav">{nav}</div><div class="muted-note">Federation Platform · Phase 7.10</div>{body_html}</div></body>
    </html>
    """


def build_json_section(title: str, data: dict) -> str:
    return f"""
    {page_header(title, data.get("report", ""))}
    <div class="card"><pre>{html.escape(json.dumps(data, indent=2, default=str))}</pre></div>
    """


def build_dashboard_body() -> str:
    data = svc.dashboard_payload()
    summary = data.get("summary", {})
    cards = metric_cards([(k.replace("_", " ").title(), v) for k, v in list(summary.items())[:6]])
    features = "".join(f"<li>{html.escape(item)}</li>" for item in data.get("features", []))
    return f"""
    {page_header("Federation Platform", "Phase 7.10 enterprise hub.")}
    {cards}
    <div class="card"><h3>Features</h3><ul>{features}</ul></div>
    """


def build_regional_hub_body() -> str:
    return build_json_section('Regional Hub', svc.regional_hub())

def build_national_hub_body() -> str:
    return build_json_section('National Hub', svc.national_hub())

def build_clinic_federation_body() -> str:
    return build_json_section('Clinic Federation', svc.clinic_federation())

def build_laboratory_federation_body() -> str:
    return build_json_section('Laboratory Federation', svc.laboratory_federation())

def build_cross_organization_exchange_body() -> str:
    return build_json_section('Cross Organization Exchange', svc.cross_organization_exchange())

def build_sync_queue_body() -> str:
    return build_json_section('Sync Queue', svc.sync_queue())

def build_federation_audit_body() -> str:
    return build_json_section('Federation Audit', svc.federation_audit())

