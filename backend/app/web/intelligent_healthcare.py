"""Intelligent Healthcare Platform web routes — Phase 8."""

from __future__ import annotations

from flask import Blueprint

from app.services.intelligent_healthcare_service import INTELLIGENT_HEALTHCARE_ROLES
from app.utils.auth import role_required
from app.web.intelligent_healthcare_lib import (
    build_dashboard_body,
    build_ai_clinical_platform_body,
    build_medical_knowledge_base_body,
    build_clinical_rules_engine_body,
    build_reference_range_engine_body,
    build_loinc_registry_body,
    build_icd10_registry_body,
    build_snomed_mapping_layer_body,
    build_drug_knowledge_layer_body,
    build_medical_ocr_platform_body,
    build_voice_clinical_platform_body,
    build_ai_copilot_hub_body,
    build_doctor_copilot_body,
    build_reception_copilot_body,
    build_collector_copilot_body,
    build_ceo_copilot_body,
    build_predictive_analytics_body,
    build_clinical_summary_body,
    build_patient_friendly_explanation_body,
    build_ai_gateway_body,
    build_llm_provider_registry_body,
    build_prompt_registry_body,
    build_prompt_versioning_body,
    build_ai_safety_layer_body,
    build_prompt_audit_body,
    build_cost_analytics_body,
    build_hallucination_detection_body,
    build_model_comparison_body,
    build_phi_redaction_body,
    build_medical_guardrails_body,
    build_clinical_recommendation_engine_body,
    build_ai_monitoring_dashboard_body,
    render_hub_page,
)

intelligent_healthcare_web_bp = Blueprint("intelligent_healthcare_web", __name__)

@intelligent_healthcare_web_bp.route("/intelligent-healthcare")
@role_required(*INTELLIGENT_HEALTHCARE_ROLES)
def intelligent_healthcare_dashboard():
    return render_hub_page("Intelligent Healthcare Platform", build_dashboard_body())
@intelligent_healthcare_web_bp.route("/intelligent-healthcare/ai-clinical-platform")
@role_required(*INTELLIGENT_HEALTHCARE_ROLES)
def intelligent_healthcare_ai_clinical_platform():
    return render_hub_page("AI Clinical Platform", build_ai_clinical_platform_body())
@intelligent_healthcare_web_bp.route("/intelligent-healthcare/medical-knowledge")
@role_required(*INTELLIGENT_HEALTHCARE_ROLES)
def intelligent_healthcare_medical_knowledge_base():
    return render_hub_page("Medical Knowledge Base", build_medical_knowledge_base_body())
@intelligent_healthcare_web_bp.route("/intelligent-healthcare/clinical-rules")
@role_required(*INTELLIGENT_HEALTHCARE_ROLES)
def intelligent_healthcare_clinical_rules_engine():
    return render_hub_page("Clinical Rules Engine", build_clinical_rules_engine_body())
@intelligent_healthcare_web_bp.route("/intelligent-healthcare/reference-ranges")
@role_required(*INTELLIGENT_HEALTHCARE_ROLES)
def intelligent_healthcare_reference_range_engine():
    return render_hub_page("Reference Range Engine", build_reference_range_engine_body())
@intelligent_healthcare_web_bp.route("/intelligent-healthcare/loinc-registry")
@role_required(*INTELLIGENT_HEALTHCARE_ROLES)
def intelligent_healthcare_loinc_registry():
    return render_hub_page("LOINC Registry", build_loinc_registry_body())
@intelligent_healthcare_web_bp.route("/intelligent-healthcare/icd10-registry")
@role_required(*INTELLIGENT_HEALTHCARE_ROLES)
def intelligent_healthcare_icd10_registry():
    return render_hub_page("ICD10 Registry", build_icd10_registry_body())
@intelligent_healthcare_web_bp.route("/intelligent-healthcare/snomed-mapping")
@role_required(*INTELLIGENT_HEALTHCARE_ROLES)
def intelligent_healthcare_snomed_mapping_layer():
    return render_hub_page("SNOMED Mapping Layer", build_snomed_mapping_layer_body())
@intelligent_healthcare_web_bp.route("/intelligent-healthcare/drug-knowledge")
@role_required(*INTELLIGENT_HEALTHCARE_ROLES)
def intelligent_healthcare_drug_knowledge_layer():
    return render_hub_page("Drug Knowledge Layer", build_drug_knowledge_layer_body())
@intelligent_healthcare_web_bp.route("/intelligent-healthcare/medical-ocr")
@role_required(*INTELLIGENT_HEALTHCARE_ROLES)
def intelligent_healthcare_medical_ocr_platform():
    return render_hub_page("Medical OCR Platform", build_medical_ocr_platform_body())
@intelligent_healthcare_web_bp.route("/intelligent-healthcare/voice-clinical")
@role_required(*INTELLIGENT_HEALTHCARE_ROLES)
def intelligent_healthcare_voice_clinical_platform():
    return render_hub_page("Voice Clinical Platform", build_voice_clinical_platform_body())
@intelligent_healthcare_web_bp.route("/intelligent-healthcare/ai-copilot")
@role_required(*INTELLIGENT_HEALTHCARE_ROLES)
def intelligent_healthcare_ai_copilot_hub():
    return render_hub_page("AI Copilot", build_ai_copilot_hub_body())
@intelligent_healthcare_web_bp.route("/intelligent-healthcare/doctor-copilot")
@role_required(*INTELLIGENT_HEALTHCARE_ROLES)
def intelligent_healthcare_doctor_copilot():
    return render_hub_page("Doctor Copilot", build_doctor_copilot_body())
@intelligent_healthcare_web_bp.route("/intelligent-healthcare/reception-copilot")
@role_required(*INTELLIGENT_HEALTHCARE_ROLES)
def intelligent_healthcare_reception_copilot():
    return render_hub_page("Reception Copilot", build_reception_copilot_body())
@intelligent_healthcare_web_bp.route("/intelligent-healthcare/collector-copilot")
@role_required(*INTELLIGENT_HEALTHCARE_ROLES)
def intelligent_healthcare_collector_copilot():
    return render_hub_page("Collector Copilot", build_collector_copilot_body())
@intelligent_healthcare_web_bp.route("/intelligent-healthcare/ceo-copilot")
@role_required(*INTELLIGENT_HEALTHCARE_ROLES)
def intelligent_healthcare_ceo_copilot():
    return render_hub_page("CEO Copilot", build_ceo_copilot_body())
@intelligent_healthcare_web_bp.route("/intelligent-healthcare/predictive-analytics")
@role_required(*INTELLIGENT_HEALTHCARE_ROLES)
def intelligent_healthcare_predictive_analytics():
    return render_hub_page("Predictive Analytics", build_predictive_analytics_body())
@intelligent_healthcare_web_bp.route("/intelligent-healthcare/clinical-summary")
@role_required(*INTELLIGENT_HEALTHCARE_ROLES)
def intelligent_healthcare_clinical_summary():
    return render_hub_page("Clinical Summary", build_clinical_summary_body())
@intelligent_healthcare_web_bp.route("/intelligent-healthcare/patient-explanation")
@role_required(*INTELLIGENT_HEALTHCARE_ROLES)
def intelligent_healthcare_patient_friendly_explanation():
    return render_hub_page("Patient-friendly Explanation", build_patient_friendly_explanation_body())
@intelligent_healthcare_web_bp.route("/intelligent-healthcare/ai-gateway")
@role_required(*INTELLIGENT_HEALTHCARE_ROLES)
def intelligent_healthcare_ai_gateway():
    return render_hub_page("AI Gateway", build_ai_gateway_body())
@intelligent_healthcare_web_bp.route("/intelligent-healthcare/llm-providers")
@role_required(*INTELLIGENT_HEALTHCARE_ROLES)
def intelligent_healthcare_llm_provider_registry():
    return render_hub_page("LLM Provider Registry", build_llm_provider_registry_body())
@intelligent_healthcare_web_bp.route("/intelligent-healthcare/prompt-registry")
@role_required(*INTELLIGENT_HEALTHCARE_ROLES)
def intelligent_healthcare_prompt_registry():
    return render_hub_page("Prompt Registry", build_prompt_registry_body())
@intelligent_healthcare_web_bp.route("/intelligent-healthcare/prompt-versioning")
@role_required(*INTELLIGENT_HEALTHCARE_ROLES)
def intelligent_healthcare_prompt_versioning():
    return render_hub_page("Prompt Versioning", build_prompt_versioning_body())
@intelligent_healthcare_web_bp.route("/intelligent-healthcare/ai-safety")
@role_required(*INTELLIGENT_HEALTHCARE_ROLES)
def intelligent_healthcare_ai_safety_layer():
    return render_hub_page("AI Safety Layer", build_ai_safety_layer_body())
@intelligent_healthcare_web_bp.route("/intelligent-healthcare/prompt-audit")
@role_required(*INTELLIGENT_HEALTHCARE_ROLES)
def intelligent_healthcare_prompt_audit():
    return render_hub_page("Prompt Audit", build_prompt_audit_body())
@intelligent_healthcare_web_bp.route("/intelligent-healthcare/cost-analytics")
@role_required(*INTELLIGENT_HEALTHCARE_ROLES)
def intelligent_healthcare_cost_analytics():
    return render_hub_page("Cost Analytics", build_cost_analytics_body())
@intelligent_healthcare_web_bp.route("/intelligent-healthcare/hallucination-detection")
@role_required(*INTELLIGENT_HEALTHCARE_ROLES)
def intelligent_healthcare_hallucination_detection():
    return render_hub_page("Hallucination Detection", build_hallucination_detection_body())
@intelligent_healthcare_web_bp.route("/intelligent-healthcare/model-comparison")
@role_required(*INTELLIGENT_HEALTHCARE_ROLES)
def intelligent_healthcare_model_comparison():
    return render_hub_page("Model Comparison", build_model_comparison_body())
@intelligent_healthcare_web_bp.route("/intelligent-healthcare/phi-redaction")
@role_required(*INTELLIGENT_HEALTHCARE_ROLES)
def intelligent_healthcare_phi_redaction():
    return render_hub_page("PHI Redaction", build_phi_redaction_body())
@intelligent_healthcare_web_bp.route("/intelligent-healthcare/medical-guardrails")
@role_required(*INTELLIGENT_HEALTHCARE_ROLES)
def intelligent_healthcare_medical_guardrails():
    return render_hub_page("Medical Guardrails", build_medical_guardrails_body())
@intelligent_healthcare_web_bp.route("/intelligent-healthcare/clinical-recommendations")
@role_required(*INTELLIGENT_HEALTHCARE_ROLES)
def intelligent_healthcare_clinical_recommendation_engine():
    return render_hub_page("Clinical Recommendation Engine", build_clinical_recommendation_engine_body())
@intelligent_healthcare_web_bp.route("/intelligent-healthcare/ai-monitoring")
@role_required(*INTELLIGENT_HEALTHCARE_ROLES)
def intelligent_healthcare_ai_monitoring_dashboard():
    return render_hub_page("AI Monitoring Dashboard", build_ai_monitoring_dashboard_body())

