"""Regional Cloud Platform web rendering helpers — Phase 9."""

from __future__ import annotations

import html
import json

from app.services import regional_cloud_service as svc
from app.web.demo_pilot_lib import metric_cards, page_header, pilot_styles

NAV = (
    ("Overview", "/regional-cloud"),
    ("Regional Deployment", "/regional-cloud/regional-deployment"),
    ("Localization", "/regional-cloud/localization"),
    ("Internationalization", "/regional-cloud/internationalization"),
    ("Language Packs", "/regional-cloud/language-packs"),
    ("Currency Engine", "/regional-cloud/currency-engine"),
    ("Tax Engine", "/regional-cloud/tax-engine"),
    ("Timezone Engine", "/regional-cloud/timezone-engine"),
    ("Holiday Engine", "/regional-cloud/holiday-engine"),
    ("Regional Compliance", "/regional-cloud/regional-compliance"),
    ("HIPAA", "/regional-cloud/hipaa"),
    ("GDPR", "/regional-cloud/gdpr"),
    ("PDPA", "/regional-cloud/pdpa"),
    ("ISO27001", "/regional-cloud/iso27001"),
    ("SOC2 Preparation", "/regional-cloud/soc2"),
    ("Geo Replication", "/regional-cloud/geo-replication"),
    ("Cross-region Federation", "/regional-cloud/cross-region-federation"),
    ("Regional Marketplace", "/regional-cloud/regional-marketplace"),
    ("Regional Partner Portal", "/regional-cloud/regional-partner-portal"),
    ("Cloud Abstraction Layer", "/regional-cloud/cloud-abstraction"),
    ("AWS", "/regional-cloud/aws"),
    ("Azure", "/regional-cloud/azure"),
    ("Google Cloud", "/regional-cloud/google-cloud"),
    ("Render", "/regional-cloud/render"),
    ("On-premise", "/regional-cloud/on-premise"),
    ("Multi-region Backup", "/regional-cloud/multi-region-backup"),
    ("Disaster Recovery", "/regional-cloud/disaster-recovery"),
    ("Regional Monitoring", "/regional-cloud/regional-monitoring"),
    ("Regional Analytics", "/regional-cloud/regional-analytics")
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
    <body><div class="wrap"><div class="nav">{nav}</div><div class="muted-note">Regional Cloud Platform · Phase 9 · Multi-country deployment with regional compliance and cloud abstraction</div>{body_html}</div></body>
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
    policy = data.get("governance", {})
    policy_html = "".join(f"<li>{html.escape(k)}: {html.escape(str(v))}</li>" for k, v in policy.items())
    return f"""
    {page_header("Regional Cloud Platform", "Phase 9 — Multi-country deployment with regional compliance and cloud abstraction.")}
    {cards}
    <div class="card"><h3>Governance</h3><ul>{policy_html}</ul></div>
    <div class="card"><h3>Modules (28)</h3><ul>{features}</ul></div>
    """


def build_regional_deployment_body() -> str:
    return build_json_section('Regional Deployment', svc.regional_deployment())

def build_localization_body() -> str:
    return build_json_section('Localization', svc.localization())

def build_internationalization_body() -> str:
    return build_json_section('Internationalization', svc.internationalization())

def build_language_packs_body() -> str:
    return build_json_section('Language Packs', svc.language_packs())

def build_currency_engine_body() -> str:
    return build_json_section('Currency Engine', svc.currency_engine())

def build_tax_engine_body() -> str:
    return build_json_section('Tax Engine', svc.tax_engine())

def build_timezone_engine_body() -> str:
    return build_json_section('Timezone Engine', svc.timezone_engine())

def build_holiday_engine_body() -> str:
    return build_json_section('Holiday Engine', svc.holiday_engine())

def build_regional_compliance_body() -> str:
    return build_json_section('Regional Compliance', svc.regional_compliance())

def build_hipaa_compliance_body() -> str:
    return build_json_section('HIPAA', svc.hipaa_compliance())

def build_gdpr_compliance_body() -> str:
    return build_json_section('GDPR', svc.gdpr_compliance())

def build_pdpa_compliance_body() -> str:
    return build_json_section('PDPA', svc.pdpa_compliance())

def build_iso27001_preparation_body() -> str:
    return build_json_section('ISO27001', svc.iso27001_preparation())

def build_soc2_preparation_body() -> str:
    return build_json_section('SOC2 Preparation', svc.soc2_preparation())

def build_geo_replication_body() -> str:
    return build_json_section('Geo Replication', svc.geo_replication())

def build_cross_region_federation_body() -> str:
    return build_json_section('Cross-region Federation', svc.cross_region_federation())

def build_regional_marketplace_body() -> str:
    return build_json_section('Regional Marketplace', svc.regional_marketplace())

def build_regional_partner_portal_body() -> str:
    return build_json_section('Regional Partner Portal', svc.regional_partner_portal())

def build_cloud_abstraction_layer_body() -> str:
    return build_json_section('Cloud Abstraction Layer', svc.cloud_abstraction_layer())

def build_aws_provider_body() -> str:
    return build_json_section('AWS', svc.aws_provider())

def build_azure_provider_body() -> str:
    return build_json_section('Azure', svc.azure_provider())

def build_google_cloud_provider_body() -> str:
    return build_json_section('Google Cloud', svc.google_cloud_provider())

def build_render_provider_body() -> str:
    return build_json_section('Render', svc.render_provider())

def build_on_premise_provider_body() -> str:
    return build_json_section('On-premise', svc.on_premise_provider())

def build_multi_region_backup_body() -> str:
    return build_json_section('Multi-region Backup', svc.multi_region_backup())

def build_disaster_recovery_body() -> str:
    return build_json_section('Disaster Recovery', svc.disaster_recovery())

def build_regional_monitoring_body() -> str:
    return build_json_section('Regional Monitoring', svc.regional_monitoring())

def build_regional_analytics_body() -> str:
    return build_json_section('Regional Analytics', svc.regional_analytics())

