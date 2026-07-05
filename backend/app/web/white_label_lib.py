"""White Label web rendering helpers — Phase 7.9."""

from __future__ import annotations

import html
import json

from app.services import white_label_service as svc
from app.web.demo_pilot_lib import metric_cards, page_header, pilot_styles

NAV = (
    ("Overview", "/white-label"),
    ("Brand Theme", "/white-label/theme"),
    ("Logo", "/white-label/logo"),
    ("Email Template", "/white-label/email"),
    ("SMS Template", "/white-label/sms"),
    ("Tenant Domain", "/white-label/domain"),
    ("Tenant Branding", "/white-label/branding"),
    ("Tenant Config", "/white-label/config")
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
    <body><div class="wrap"><div class="nav">{nav}</div><div class="muted-note">White Label · Phase 7.9</div>{body_html}</div></body>
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
    {page_header("White Label", "Phase 7.9 enterprise hub.")}
    {cards}
    <div class="card"><h3>Features</h3><ul>{features}</ul></div>
    """


def build_brand_theme_body() -> str:
    return build_json_section('Brand Theme', svc.brand_theme())

def build_brand_logo_body() -> str:
    return build_json_section('Logo', svc.brand_logo())

def build_email_template_body() -> str:
    return build_json_section('Email Template', svc.email_template())

def build_sms_template_body() -> str:
    return build_json_section('SMS Template', svc.sms_template())

def build_tenant_domain_body() -> str:
    return build_json_section('Tenant Domain', svc.tenant_domain())

def build_tenant_branding_body() -> str:
    return build_json_section('Tenant Branding', svc.tenant_branding())

def build_tenant_config_body() -> str:
    return build_json_section('Tenant Config', svc.tenant_config())

