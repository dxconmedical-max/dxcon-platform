"""Intelligent Healthcare Platform API routes — Phase 8."""

from __future__ import annotations

from flask import Blueprint

from app.services.intelligent_healthcare_service import (
    dashboard_payload,
    ai_clinical_platform,
    medical_knowledge_base,
    clinical_rules_engine,
    reference_range_engine,
    loinc_registry,
    icd10_registry,
    snomed_mapping_layer,
    drug_knowledge_layer,
    medical_ocr_platform,
    voice_clinical_platform,
    ai_copilot_hub,
    doctor_copilot,
    reception_copilot,
    collector_copilot,
    ceo_copilot,
    predictive_analytics,
    clinical_summary,
    patient_friendly_explanation,
    ai_gateway,
    llm_provider_registry,
    prompt_registry,
    prompt_versioning,
    ai_safety_layer,
    prompt_audit,
    cost_analytics,
    hallucination_detection,
    model_comparison,
    phi_redaction,
    medical_guardrails,
    clinical_recommendation_engine,
    ai_monitoring_dashboard,
    intelligent_healthcare_readiness_report,
)

intelligent_healthcare_bp = Blueprint("intelligent_healthcare_api", __name__, url_prefix="/api/v1/intelligent-healthcare")

@intelligent_healthcare_bp.route("/dashboard", methods=["GET"])
def intelligent_healthcare_dashboard_api():
    return dashboard_payload()

@intelligent_healthcare_bp.route("/ai-clinical-platform", methods=["GET"])
def intelligent_healthcare_ai_clinical_platform_api():
    return ai_clinical_platform()

@intelligent_healthcare_bp.route("/medical-knowledge", methods=["GET"])
def intelligent_healthcare_medical_knowledge_base_api():
    return medical_knowledge_base()

@intelligent_healthcare_bp.route("/clinical-rules", methods=["GET"])
def intelligent_healthcare_clinical_rules_engine_api():
    return clinical_rules_engine()

@intelligent_healthcare_bp.route("/reference-ranges", methods=["GET"])
def intelligent_healthcare_reference_range_engine_api():
    return reference_range_engine()

@intelligent_healthcare_bp.route("/loinc-registry", methods=["GET"])
def intelligent_healthcare_loinc_registry_api():
    return loinc_registry()

@intelligent_healthcare_bp.route("/icd10-registry", methods=["GET"])
def intelligent_healthcare_icd10_registry_api():
    return icd10_registry()

@intelligent_healthcare_bp.route("/snomed-mapping", methods=["GET"])
def intelligent_healthcare_snomed_mapping_layer_api():
    return snomed_mapping_layer()

@intelligent_healthcare_bp.route("/drug-knowledge", methods=["GET"])
def intelligent_healthcare_drug_knowledge_layer_api():
    return drug_knowledge_layer()

@intelligent_healthcare_bp.route("/medical-ocr", methods=["GET"])
def intelligent_healthcare_medical_ocr_platform_api():
    return medical_ocr_platform()

@intelligent_healthcare_bp.route("/voice-clinical", methods=["GET"])
def intelligent_healthcare_voice_clinical_platform_api():
    return voice_clinical_platform()

@intelligent_healthcare_bp.route("/ai-copilot", methods=["GET"])
def intelligent_healthcare_ai_copilot_hub_api():
    return ai_copilot_hub()

@intelligent_healthcare_bp.route("/doctor-copilot", methods=["GET"])
def intelligent_healthcare_doctor_copilot_api():
    return doctor_copilot()

@intelligent_healthcare_bp.route("/reception-copilot", methods=["GET"])
def intelligent_healthcare_reception_copilot_api():
    return reception_copilot()

@intelligent_healthcare_bp.route("/collector-copilot", methods=["GET"])
def intelligent_healthcare_collector_copilot_api():
    return collector_copilot()

@intelligent_healthcare_bp.route("/ceo-copilot", methods=["GET"])
def intelligent_healthcare_ceo_copilot_api():
    return ceo_copilot()

@intelligent_healthcare_bp.route("/predictive-analytics", methods=["GET"])
def intelligent_healthcare_predictive_analytics_api():
    return predictive_analytics()

@intelligent_healthcare_bp.route("/clinical-summary", methods=["GET"])
def intelligent_healthcare_clinical_summary_api():
    return clinical_summary()

@intelligent_healthcare_bp.route("/patient-explanation", methods=["GET"])
def intelligent_healthcare_patient_friendly_explanation_api():
    return patient_friendly_explanation()

@intelligent_healthcare_bp.route("/ai-gateway", methods=["GET"])
def intelligent_healthcare_ai_gateway_api():
    return ai_gateway()

@intelligent_healthcare_bp.route("/llm-providers", methods=["GET"])
def intelligent_healthcare_llm_provider_registry_api():
    return llm_provider_registry()

@intelligent_healthcare_bp.route("/prompt-registry", methods=["GET"])
def intelligent_healthcare_prompt_registry_api():
    return prompt_registry()

@intelligent_healthcare_bp.route("/prompt-versioning", methods=["GET"])
def intelligent_healthcare_prompt_versioning_api():
    return prompt_versioning()

@intelligent_healthcare_bp.route("/ai-safety", methods=["GET"])
def intelligent_healthcare_ai_safety_layer_api():
    return ai_safety_layer()

@intelligent_healthcare_bp.route("/prompt-audit", methods=["GET"])
def intelligent_healthcare_prompt_audit_api():
    return prompt_audit()

@intelligent_healthcare_bp.route("/cost-analytics", methods=["GET"])
def intelligent_healthcare_cost_analytics_api():
    return cost_analytics()

@intelligent_healthcare_bp.route("/hallucination-detection", methods=["GET"])
def intelligent_healthcare_hallucination_detection_api():
    return hallucination_detection()

@intelligent_healthcare_bp.route("/model-comparison", methods=["GET"])
def intelligent_healthcare_model_comparison_api():
    return model_comparison()

@intelligent_healthcare_bp.route("/phi-redaction", methods=["GET"])
def intelligent_healthcare_phi_redaction_api():
    return phi_redaction()

@intelligent_healthcare_bp.route("/medical-guardrails", methods=["GET"])
def intelligent_healthcare_medical_guardrails_api():
    return medical_guardrails()

@intelligent_healthcare_bp.route("/clinical-recommendations", methods=["GET"])
def intelligent_healthcare_clinical_recommendation_engine_api():
    return clinical_recommendation_engine()

@intelligent_healthcare_bp.route("/ai-monitoring", methods=["GET"])
def intelligent_healthcare_ai_monitoring_dashboard_api():
    return ai_monitoring_dashboard()

@intelligent_healthcare_bp.route("/readiness", methods=["GET"])
def intelligent_healthcare_readiness_api():
    return intelligent_healthcare_readiness_report()
