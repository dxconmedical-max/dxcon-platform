"""Healthcare Ecosystem web rendering helpers — Phase 10."""

from __future__ import annotations

import html
import json

from app.services import healthcare_ecosystem_service as svc
from app.web.demo_pilot_lib import metric_cards, page_header, pilot_styles

NAV = (
    ("Overview", "/healthcare-ecosystem"),
    ("DxCon Lab", "/healthcare-ecosystem/dxcon-lab"),
    ("DxCon Clinic", "/healthcare-ecosystem/dxcon-clinic"),
    ("DxCon Home", "/healthcare-ecosystem/dxcon-home"),
    ("DxCon Pharmacy", "/healthcare-ecosystem/dxcon-pharmacy"),
    ("DxCon Insurance", "/healthcare-ecosystem/dxcon-insurance"),
    ("DxCon AI", "/healthcare-ecosystem/dxcon-ai"),
    ("DxCon Cloud", "/healthcare-ecosystem/dxcon-cloud"),
    ("DxCon Marketplace", "/healthcare-ecosystem/dxcon-marketplace"),
    ("Partner Portal", "/healthcare-ecosystem/partner-portal"),
    ("Customer Portal", "/healthcare-ecosystem/customer-portal"),
    ("Enterprise Governance", "/healthcare-ecosystem/enterprise-governance"),
    ("Architecture Board", "/healthcare-ecosystem/architecture-board"),
    ("Release Board", "/healthcare-ecosystem/release-board"),
    ("Medical Governance", "/healthcare-ecosystem/medical-governance"),
    ("Security Governance", "/healthcare-ecosystem/security-governance"),
    ("AI Governance", "/healthcare-ecosystem/ai-governance"),
    ("Enterprise Audit", "/healthcare-ecosystem/enterprise-audit"),
    ("Customer Success Portal", "/healthcare-ecosystem/customer-success"),
    ("Training Center", "/healthcare-ecosystem/training-center"),
    ("Certification Center", "/healthcare-ecosystem/certification-center"),
    ("Release Manager", "/healthcare-ecosystem/release-manager"),
    ("License Manager", "/healthcare-ecosystem/license-manager"),
    ("Commercial Readiness", "/healthcare-ecosystem/commercial-readiness"),
    ("Support Center", "/healthcare-ecosystem/support-center"),
    ("Knowledge Base", "/healthcare-ecosystem/knowledge-base")
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
    <body><div class="wrap"><div class="nav">{nav}</div><div class="muted-note">Healthcare Ecosystem · Phase 10 · DxCon Enterprise v1.0 commercial release ecosystem</div>{body_html}</div></body>
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
    release = data.get("release", {})
    release_html = "".join(f"<li>{html.escape(k)}: {html.escape(str(v))}</li>" for k, v in release.items())
    return f"""
    {page_header("Healthcare Ecosystem", "Phase 10 — DxCon Enterprise v1.0 commercial release ecosystem.")}
    {cards}
    <div class="card"><h3>Release</h3><ul>{release_html}</ul></div>
    <div class="card"><h3>Ecosystem (25)</h3><ul>{features}</ul></div>
    """


def build_dxcon_lab_body() -> str:
    return build_json_section('DxCon Lab', svc.dxcon_lab())

def build_dxcon_clinic_body() -> str:
    return build_json_section('DxCon Clinic', svc.dxcon_clinic())

def build_dxcon_home_body() -> str:
    return build_json_section('DxCon Home', svc.dxcon_home())

def build_dxcon_pharmacy_body() -> str:
    return build_json_section('DxCon Pharmacy', svc.dxcon_pharmacy())

def build_dxcon_insurance_body() -> str:
    return build_json_section('DxCon Insurance', svc.dxcon_insurance())

def build_dxcon_ai_body() -> str:
    return build_json_section('DxCon AI', svc.dxcon_ai())

def build_dxcon_cloud_body() -> str:
    return build_json_section('DxCon Cloud', svc.dxcon_cloud())

def build_dxcon_marketplace_body() -> str:
    return build_json_section('DxCon Marketplace', svc.dxcon_marketplace())

def build_partner_portal_body() -> str:
    return build_json_section('Partner Portal', svc.partner_portal())

def build_customer_portal_body() -> str:
    return build_json_section('Customer Portal', svc.customer_portal())

def build_enterprise_governance_body() -> str:
    return build_json_section('Enterprise Governance', svc.enterprise_governance())

def build_architecture_board_body() -> str:
    return build_json_section('Architecture Board', svc.architecture_board())

def build_release_board_body() -> str:
    return build_json_section('Release Board', svc.release_board())

def build_medical_governance_body() -> str:
    return build_json_section('Medical Governance', svc.medical_governance())

def build_security_governance_body() -> str:
    return build_json_section('Security Governance', svc.security_governance())

def build_ai_governance_body() -> str:
    return build_json_section('AI Governance', svc.ai_governance())

def build_enterprise_audit_body() -> str:
    return build_json_section('Enterprise Audit', svc.enterprise_audit())

def build_customer_success_portal_body() -> str:
    return build_json_section('Customer Success Portal', svc.customer_success_portal())

def build_training_center_body() -> str:
    return build_json_section('Training Center', svc.training_center())

def build_certification_center_body() -> str:
    return build_json_section('Certification Center', svc.certification_center())

def build_release_manager_body() -> str:
    return build_json_section('Release Manager', svc.release_manager())

def build_license_manager_body() -> str:
    return build_json_section('License Manager', svc.license_manager())

def build_commercial_readiness_body() -> str:
    return build_json_section('Commercial Readiness', svc.commercial_readiness())

def build_support_center_body() -> str:
    return build_json_section('Support Center', svc.support_center())

def build_knowledge_base_body() -> str:
    return build_json_section('Knowledge Base', svc.knowledge_base())

