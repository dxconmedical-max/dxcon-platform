"""Population Health web rendering helpers — Phase 7.8."""

from __future__ import annotations

import html
import json

from app.services import population_health_service as svc
from app.web.demo_pilot_lib import metric_cards, page_header, pilot_styles

NAV = (
    ("Overview", "/population-health"),
    ("Disease Registry", "/population-health/registry"),
    ("Population Dashboard", "/population-health/dashboard"),
    ("Risk Groups", "/population-health/risk-groups"),
    ("Vaccination Statistics", "/population-health/vaccination"),
    ("Diabetes", "/population-health/diabetes"),
    ("Hypertension", "/population-health/hypertension"),
    ("Cancer", "/population-health/cancer"),
    ("Women's Health", "/population-health/womens-health"),
    ("Children", "/population-health/children")
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
    <body><div class="wrap"><div class="nav">{nav}</div><div class="muted-note">Population Health · Phase 7.8</div>{body_html}</div></body>
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
    {page_header("Population Health", "Phase 7.8 enterprise hub.")}
    {cards}
    <div class="card"><h3>Features</h3><ul>{features}</ul></div>
    """


def build_disease_registry_body() -> str:
    return build_json_section('Disease Registry', svc.disease_registry())

def build_population_dashboard_body() -> str:
    return build_json_section('Population Dashboard', svc.population_dashboard())

def build_risk_groups_body() -> str:
    return build_json_section('Risk Groups', svc.risk_groups())

def build_vaccination_statistics_body() -> str:
    return build_json_section('Vaccination Statistics', svc.vaccination_statistics())

def build_diabetes_panel_body() -> str:
    return build_json_section('Diabetes', svc.diabetes_panel())

def build_hypertension_panel_body() -> str:
    return build_json_section('Hypertension', svc.hypertension_panel())

def build_cancer_panel_body() -> str:
    return build_json_section('Cancer', svc.cancer_panel())

def build_womens_health_panel_body() -> str:
    return build_json_section("Women's Health", svc.womens_health_panel())

def build_children_panel_body() -> str:
    return build_json_section('Children', svc.children_panel())

