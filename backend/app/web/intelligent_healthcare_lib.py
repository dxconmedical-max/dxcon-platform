"""Intelligent Healthcare Platform web rendering helpers — Phase 8."""

from __future__ import annotations

import html
import json

from app.services import intelligent_healthcare_service as svc
from app.web.demo_pilot_lib import metric_cards, page_header, pilot_styles

NAV = (
    ("Overview", "/intelligent-healthcare"),
    ("AI Clinical Platform", "/intelligent-healthcare/ai-clinical-platform"),
    ("Medical Knowledge Base", "/intelligent-healthcare/medical-knowledge"),
    ("Clinical Rules Engine", "/intelligent-healthcare/clinical-rules"),
    ("Reference Range Engine", "/intelligent-healthcare/reference-ranges"),
    ("LOINC Registry", "/intelligent-healthcare/loinc-registry"),
    ("ICD10 Registry", "/intelligent-healthcare/icd10-registry"),
    ("SNOMED Mapping Layer", "/intelligent-healthcare/snomed-mapping"),
    ("Drug Knowledge Layer", "/intelligent-healthcare/drug-knowledge"),
    ("Medical OCR Platform", "/intelligent-healthcare/medical-ocr"),
    ("Voice Clinical Platform", "/intelligent-healthcare/voice-clinical"),
    ("AI Copilot", "/intelligent-healthcare/ai-copilot"),
    ("Doctor Copilot", "/intelligent-healthcare/doctor-copilot"),
    ("Reception Copilot", "/intelligent-healthcare/reception-copilot"),
    ("Collector Copilot", "/intelligent-healthcare/collector-copilot"),
    ("CEO Copilot", "/intelligent-healthcare/ceo-copilot"),
    ("Predictive Analytics", "/intelligent-healthcare/predictive-analytics"),
    ("Clinical Summary", "/intelligent-healthcare/clinical-summary"),
    ("Patient-friendly Explanation", "/intelligent-healthcare/patient-explanation"),
    ("AI Gateway", "/intelligent-healthcare/ai-gateway"),
    ("LLM Provider Registry", "/intelligent-healthcare/llm-providers"),
    ("Prompt Registry", "/intelligent-healthcare/prompt-registry"),
    ("Prompt Versioning", "/intelligent-healthcare/prompt-versioning"),
    ("AI Safety Layer", "/intelligent-healthcare/ai-safety"),
    ("Prompt Audit", "/intelligent-healthcare/prompt-audit"),
    ("Cost Analytics", "/intelligent-healthcare/cost-analytics"),
    ("Hallucination Detection", "/intelligent-healthcare/hallucination-detection"),
    ("Model Comparison", "/intelligent-healthcare/model-comparison"),
    ("PHI Redaction", "/intelligent-healthcare/phi-redaction"),
    ("Medical Guardrails", "/intelligent-healthcare/medical-guardrails"),
    ("Clinical Recommendation Engine", "/intelligent-healthcare/clinical-recommendations"),
    ("AI Monitoring Dashboard", "/intelligent-healthcare/ai-monitoring")
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
    <body><div class="wrap"><div class="nav">{nav}</div><div class="muted-note">Intelligent Healthcare Platform · Phase 8 · Human medical review mandatory</div>{body_html}</div></body>
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
    policy = data.get("policy", {})
    policy_html = "".join(f"<li>{html.escape(k)}: {html.escape(str(v))}</li>" for k, v in policy.items())
    return f"""
    {page_header("Intelligent Healthcare Platform", "Phase 8 — AI-assisted healthcare with mandatory human review.")}
    {cards}
    <div class="card"><h3>Governance Policy</h3><ul>{policy_html}</ul></div>
    <div class="card"><h3>Modules (31)</h3><ul>{features}</ul></div>
    """


def build_ai_clinical_platform_body() -> str:
    return build_json_section('AI Clinical Platform', svc.ai_clinical_platform())

def build_medical_knowledge_base_body() -> str:
    return build_json_section('Medical Knowledge Base', svc.medical_knowledge_base())

def build_clinical_rules_engine_body() -> str:
    return build_json_section('Clinical Rules Engine', svc.clinical_rules_engine())

def build_reference_range_engine_body() -> str:
    return build_json_section('Reference Range Engine', svc.reference_range_engine())

def build_loinc_registry_body() -> str:
    return build_json_section('LOINC Registry', svc.loinc_registry())

def build_icd10_registry_body() -> str:
    return build_json_section('ICD10 Registry', svc.icd10_registry())

def build_snomed_mapping_layer_body() -> str:
    return build_json_section('SNOMED Mapping Layer', svc.snomed_mapping_layer())

def build_drug_knowledge_layer_body() -> str:
    return build_json_section('Drug Knowledge Layer', svc.drug_knowledge_layer())

def build_medical_ocr_platform_body() -> str:
    return build_json_section('Medical OCR Platform', svc.medical_ocr_platform())

def build_voice_clinical_platform_body() -> str:
    return build_json_section('Voice Clinical Platform', svc.voice_clinical_platform())

def build_ai_copilot_hub_body() -> str:
    return build_json_section('AI Copilot', svc.ai_copilot_hub())

def build_doctor_copilot_body() -> str:
    return build_json_section('Doctor Copilot', svc.doctor_copilot())

def build_reception_copilot_body() -> str:
    return build_json_section('Reception Copilot', svc.reception_copilot())

def build_collector_copilot_body() -> str:
    return build_json_section('Collector Copilot', svc.collector_copilot())

def build_ceo_copilot_body() -> str:
    return build_json_section('CEO Copilot', svc.ceo_copilot())

def build_predictive_analytics_body() -> str:
    return build_json_section('Predictive Analytics', svc.predictive_analytics())

def build_clinical_summary_body() -> str:
    return build_json_section('Clinical Summary', svc.clinical_summary())

def build_patient_friendly_explanation_body() -> str:
    return build_json_section('Patient-friendly Explanation', svc.patient_friendly_explanation())

def build_ai_gateway_body() -> str:
    return build_json_section('AI Gateway', svc.ai_gateway())

def build_llm_provider_registry_body() -> str:
    return build_json_section('LLM Provider Registry', svc.llm_provider_registry())

def build_prompt_registry_body() -> str:
    return build_json_section('Prompt Registry', svc.prompt_registry())

def build_prompt_versioning_body() -> str:
    return build_json_section('Prompt Versioning', svc.prompt_versioning())

def build_ai_safety_layer_body() -> str:
    return build_json_section('AI Safety Layer', svc.ai_safety_layer())

def build_prompt_audit_body() -> str:
    return build_json_section('Prompt Audit', svc.prompt_audit())

def build_cost_analytics_body() -> str:
    return build_json_section('Cost Analytics', svc.cost_analytics())

def build_hallucination_detection_body() -> str:
    return build_json_section('Hallucination Detection', svc.hallucination_detection())

def build_model_comparison_body() -> str:
    return build_json_section('Model Comparison', svc.model_comparison())

def build_phi_redaction_body() -> str:
    return build_json_section('PHI Redaction', svc.phi_redaction())

def build_medical_guardrails_body() -> str:
    return build_json_section('Medical Guardrails', svc.medical_guardrails())

def build_clinical_recommendation_engine_body() -> str:
    return build_json_section('Clinical Recommendation Engine', svc.clinical_recommendation_engine())

def build_ai_monitoring_dashboard_body() -> str:
    return build_json_section('AI Monitoring Dashboard', svc.ai_monitoring_dashboard())

