"""AI Copilot Platform web rendering helpers — Phase 7.3."""

from __future__ import annotations

import html
import json

from app.services import ai_copilot_service as svc
from app.web.demo_pilot_lib import metric_cards, page_header, pilot_styles

NAV = (
    ("Overview", "/ai-copilot"),
    ("Reception Copilot", "/ai-copilot/reception-copilot"),
    ("Doctor Copilot", "/ai-copilot/doctor-copilot"),
    ("Collector Copilot", "/ai-copilot/collector-copilot"),
    ("Lab Copilot", "/ai-copilot/lab-copilot"),
    ("CEO Copilot", "/ai-copilot/ceo-copilot"),
    ("Prompt Registry", "/ai-copilot/prompts"),
    ("Prompt Version", "/ai-copilot/prompt-versions"),
    ("Conversation Audit", "/ai-copilot/audit"),
    ("Safety Layer", "/ai-copilot/safety"),
    ("PHI Redaction", "/ai-copilot/phi-redaction"),
    ("AI Routing", "/ai-copilot/routing")
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
    <body><div class="wrap"><div class="nav">{nav}</div><div class="muted-note">AI Copilot Platform · Phase 7.3</div>{body_html}</div></body>
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
    {page_header("AI Copilot Platform", "Phase 7.3 enterprise hub.")}
    {cards}
    <div class="card"><h3>Features</h3><ul>{features}</ul></div>
    """


def build_reception_copilot_body() -> str:
    return build_json_section('Reception Copilot', svc.reception_copilot())

def build_doctor_copilot_body() -> str:
    return build_json_section('Doctor Copilot', svc.doctor_copilot())

def build_collector_copilot_body() -> str:
    return build_json_section('Collector Copilot', svc.collector_copilot())

def build_lab_copilot_body() -> str:
    return build_json_section('Lab Copilot', svc.lab_copilot())

def build_ceo_copilot_body() -> str:
    return build_json_section('CEO Copilot', svc.ceo_copilot())

def build_prompt_registry_view_body() -> str:
    return build_json_section('Prompt Registry', svc.prompt_registry_view())

def build_prompt_version_view_body() -> str:
    return build_json_section('Prompt Version', svc.prompt_version_view())

def build_conversation_audit_body() -> str:
    return build_json_section('Conversation Audit', svc.conversation_audit())

def build_safety_layer_body() -> str:
    return build_json_section('Safety Layer', svc.safety_layer())

def build_phi_redaction_demo_body() -> str:
    return build_json_section('PHI Redaction', svc.phi_redaction_demo())

def build_ai_routing_body() -> str:
    return build_json_section('AI Routing', svc.ai_routing())

