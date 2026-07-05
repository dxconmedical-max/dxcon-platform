"""Intelligent Healthcare Platform business logic for Phase 8."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from app.ai_platform.audit import AIAuditService
from app.ai_platform.metrics import AIUsageMetricsService
from app.ai_platform.phi_redaction import redact_phi
from app.ai_platform.prompt_registry import PromptRegistry
from app.ai_platform.registry import AIProviderRegistry
from app.ai_platform.router import ModelRouter
from app.ai_platform.safety import AISafetyPolicy, BLOCKED_PATTERNS, CLINICAL_DISCLAIMER
from app.services.ai_cds_service import ClinicalRuleEngineService
from app.services.ai_clinical_service import ensure_clinical, dashboard_payload as ai_clinical_dashboard
from app.services.ai_copilot_service import (
    ceo_copilot as _ceo_copilot,
    collector_copilot as _collector_copilot,
    doctor_copilot as _doctor_copilot,
    reception_copilot as _reception_copilot,
)
from app.services.ai_operations_service import ai_cost_metrics, ai_usage_metrics
from app.services.healthcare_standards_service import CodeMappingService, HealthcareStandardsService
from app.services.interpretation_engine_service import ReferenceRangeService
from app.services.knowledge_engine_service import (
    RULE_CHAINS,
    DiseaseMappingService,
    GuidelinePackService,
)
from app.services.standards_advanced_service import validate_icd10, validate_loinc
from app.services.voice_platform_service import voice_session
from app.models.ai_cds import ClinicalGuidelinePack
from app.standards.mapping import StandardsMappingService

INTELLIGENT_HEALTHCARE_ROLES = ("SUPER_ADMIN", "ADMIN", "DOCTOR")

GOVERNANCE_POLICY = {
    "advisory_only": True,
    "automatic_diagnosis": False,
    "human_review_required": True,
    "clinical_disclaimer": CLINICAL_DISCLAIMER,
    "postgresql_only": True,
    "backward_compatible": True,
    "destructive_migrations": False,
}

FEATURES = (
    "AI Clinical Platform",
    "Medical Knowledge Base",
    "Clinical Rules Engine",
    "Reference Range Engine",
    "LOINC Registry",
    "ICD10 Registry",
    "SNOMED Mapping Layer",
    "Drug Knowledge Layer",
    "Medical OCR Platform",
    "Voice Clinical Platform",
    "AI Copilot",
    "Doctor Copilot",
    "Reception Copilot",
    "Collector Copilot",
    "CEO Copilot",
    "Predictive Analytics",
    "Clinical Summary",
    "Patient-friendly Explanation",
    "AI Gateway",
    "LLM Provider Registry",
    "Prompt Registry",
    "Prompt Versioning",
    "AI Safety Layer",
    "Prompt Audit",
    "Cost Analytics",
    "Hallucination Detection",
    "Model Comparison",
    "PHI Redaction",
    "Medical Guardrails",
    "Clinical Recommendation Engine",
    "AI Monitoring Dashboard",
)

DRUG_KNOWLEDGE_SCAFFOLD = (
    {"code": "METFORMIN", "name": "Metformin", "class": "Antidiabetic", "interaction_check": True},
    {"code": "LISINOPRIL", "name": "Lisinopril", "class": "ACE inhibitor", "interaction_check": True},
    {"code": "ATORVASTATIN", "name": "Atorvastatin", "class": "Statin", "interaction_check": True},
)

OCR_PIPELINES = ("lab_requisition", "insurance_card", "prescription", "result_report")


def _advisory(payload: dict[str, Any], *, report: str, task_type: str = "general") -> dict[str, Any]:
    wrapped = AISafetyPolicy.wrap_output(payload, task_type=task_type)
    wrapped["report"] = report
    wrapped["doctor_review_required"] = True
    return wrapped


def ensure_intelligent_healthcare() -> dict[str, Any]:
    ensure_clinical()
    AIProviderRegistry.ensure_defaults()
    PromptRegistry.ensure_defaults()
    ClinicalRuleEngineService.ensure_default_packs()
    return {"ready": True, **GOVERNANCE_POLICY}


def ai_clinical_platform() -> dict[str, Any]:
    ensure_intelligent_healthcare()
    dash = ai_clinical_dashboard()
    return _advisory(
        {"platform": dash["platform"], "summary": dash["summary"], "legacy_route": "/ai-clinical"},
        report="ai_clinical_platform",
        task_type="interpretation",
    )


def medical_knowledge_base() -> dict[str, Any]:
    ensure_intelligent_healthcare()
    guidelines = GuidelinePackService.list_guidelines(page_size=5)
    diseases = DiseaseMappingService.list_diseases(page_size=5)
    return {
        "report": "medical_knowledge_base",
        "guidelines_count": guidelines.get("total", 0),
        "diseases_count": diseases.get("total", 0),
        "rule_chains": len(RULE_CHAINS),
        "legacy_routes": ["/knowledge", "/api/v1/guidelines", "/api/v1/diseases"],
    }


def clinical_rules_engine() -> dict[str, Any]:
    ensure_intelligent_healthcare()
    pack_count = ClinicalGuidelinePack.query.count()
    return _advisory(
        {"packs": pack_count, "engine": "ClinicalRuleEngineService", "legacy_route": "/api/v1/ai-cds"},
        report="clinical_rules_engine",
        task_type="interpretation",
    )


def reference_range_engine() -> dict[str, Any]:
    ensure_intelligent_healthcare()
    ranges = ReferenceRangeService.list_ranges()
    return {
        "report": "reference_range_engine",
        "ranges_count": len(ranges),
        "legacy_route": "/api/v1/reference-ranges",
    }


def loinc_registry() -> dict[str, Any]:
    ensure_intelligent_healthcare()
    sample = validate_loinc("2345-7")
    systems = HealthcareStandardsService.list_code_systems()
    loinc = next((s for s in systems.get("systems", []) if s.get("system_code") == "LOINC"), {})
    return {
        "report": "loinc_registry",
        "system": loinc,
        "sample_validation": sample,
        "legacy_route": "/standards-advanced/loinc",
    }


def icd10_registry() -> dict[str, Any]:
    ensure_intelligent_healthcare()
    sample = validate_icd10("E11.9")
    return {
        "report": "icd10_registry",
        "sample_validation": sample,
        "legacy_route": "/standards-advanced/icd10",
    }


def snomed_mapping_layer() -> dict[str, Any]:
    ensure_intelligent_healthcare()
    resolved = StandardsMappingService.resolve("LOINC", "2345-7", "SNOMED_CT")
    mappings = CodeMappingService.list_mappings(target_system="SNOMED_CT")
    return {
        "report": "snomed_mapping_layer",
        "sample_resolution": resolved,
        "mappings_count": mappings.get("count", 0),
        "legacy_route": "/api/v1/standards/mappings",
    }


def drug_knowledge_layer() -> dict[str, Any]:
    ensure_intelligent_healthcare()
    return {
        "report": "drug_knowledge_layer",
        "status": "SCAFFOLD",
        "drugs": list(DRUG_KNOWLEDGE_SCAFFOLD),
        "interaction_check": True,
        "note": "Extend knowledge_engine for full RxNorm integration",
    }


def medical_ocr_platform() -> dict[str, Any]:
    ensure_intelligent_healthcare()
    return {
        "report": "medical_ocr_platform",
        "status": "SCAFFOLD",
        "pipelines": list(OCR_PIPELINES),
        "human_review_required": True,
        "phi_redaction_before_storage": True,
    }


def voice_clinical_platform() -> dict[str, Any]:
    ensure_intelligent_healthcare()
    session = voice_session()
    return _advisory(
        {"voice": session, "legacy_route": "/voice-platform"},
        report="voice_clinical_platform",
        task_type="summary",
    )


def ai_copilot_hub() -> dict[str, Any]:
    ensure_intelligent_healthcare()
    return {
        "report": "ai_copilot_hub",
        "copilots": ["reception", "doctor", "collector", "lab", "ceo"],
        "advisory_only": True,
        "legacy_route": "/ai-copilot",
    }


def doctor_copilot() -> dict[str, Any]:
    return _advisory(_doctor_copilot(), report="doctor_copilot", task_type="interpretation")


def reception_copilot() -> dict[str, Any]:
    return _advisory(_reception_copilot(), report="reception_copilot", task_type="general")


def collector_copilot() -> dict[str, Any]:
    return _advisory(_collector_copilot(), report="collector_copilot", task_type="general")


def ceo_copilot() -> dict[str, Any]:
    return _advisory(_ceo_copilot(), report="ceo_copilot", task_type="summary")


def predictive_analytics() -> dict[str, Any]:
    ensure_intelligent_healthcare()
    return _advisory(
        {
            "models": ["risk_stratification", "readmission_risk", "panel_trend"],
            "status": "READY",
            "legacy_routes": ["/population-health", "/api/v1/enterprise-analytics/dashboard"],
        },
        report="predictive_analytics",
        task_type="risk",
    )


def clinical_summary() -> dict[str, Any]:
    ensure_intelligent_healthcare()
    return _advisory(
        {"template": "clinical_summary_v1", "sections": ["overview", "abnormal_results", "recommendations"]},
        report="clinical_summary",
        task_type="summary",
    )


def patient_friendly_explanation() -> dict[str, Any]:
    ensure_intelligent_healthcare()
    return _advisory(
        {"reading_level": "grade_8", "language": "vi-VN", "template": "patient_friendly_v1"},
        report="patient_friendly_explanation",
        task_type="patient_friendly",
    )


def ai_gateway() -> dict[str, Any]:
    ensure_intelligent_healthcare()
    providers = AIProviderRegistry.list_providers()
    return {
        "report": "ai_gateway",
        "providers": providers.get("count", 0),
        "default_routes": ModelRouter.DEFAULT_ROUTES,
        "legacy_route": "/api/v1/ai-platform",
    }


def llm_provider_registry() -> dict[str, Any]:
    ensure_intelligent_healthcare()
    return {"report": "llm_provider_registry", **AIProviderRegistry.list_providers()}


def prompt_registry() -> dict[str, Any]:
    ensure_intelligent_healthcare()
    return {"report": "prompt_registry", **PromptRegistry.list_prompts()}


def prompt_versioning() -> dict[str, Any]:
    ensure_intelligent_healthcare()
    from app.ai_platform.models import PromptVersion

    prompts = PromptRegistry.list_prompts()
    version_count = PromptVersion.query.count()
    return {
        "report": "prompt_versioning",
        "prompts": prompts.get("count", 0),
        "versions_total": version_count,
    }


def ai_safety_layer() -> dict[str, Any]:
    ensure_intelligent_healthcare()
    return {
        "report": "ai_safety_layer",
        "blocked_patterns": list(BLOCKED_PATTERNS),
        "disclaimer": CLINICAL_DISCLAIMER,
        "sample_check": AISafetyPolicy.check_request("interpretation", {"text": "review result"}),
    }


def prompt_audit() -> dict[str, Any]:
    ensure_intelligent_healthcare()
    audit = AIAuditService.list_entries(page_size=10)
    return {"report": "prompt_audit", "audit_entries": audit.get("count", 0), "recent": audit.get("entries", [])}


def cost_analytics() -> dict[str, Any]:
    ensure_intelligent_healthcare()
    return {"report": "cost_analytics", **ai_cost_metrics(), "legacy_route": "/ai-operations"}


def hallucination_detection() -> dict[str, Any]:
    ensure_intelligent_healthcare()
    return {
        "report": "hallucination_detection",
        "status": "READY",
        "checks": ["citation_required", "confidence_threshold", "blocked_patterns", "human_review_flag"],
        "blocked_patterns": list(BLOCKED_PATTERNS),
    }


def model_comparison() -> dict[str, Any]:
    ensure_intelligent_healthcare()
    providers = AIProviderRegistry.list_providers().get("providers", [])
    comparisons = []
    for provider in providers[:3]:
        route = ModelRouter.route("interpretation")
        comparisons.append(
            {
                "provider": provider.get("name"),
                "model": provider.get("default_model"),
                "routed_provider_type": route.get("provider_type"),
            }
        )
    return {"report": "model_comparison", "comparisons": comparisons, "task_type": "interpretation"}


def phi_redaction() -> dict[str, Any]:
    ensure_intelligent_healthcare()
    sample = "Patient Nguyen Van A, DOB 1980-01-01, MRN 12345"
    return {
        "report": "phi_redaction",
        "sample_input": sample,
        "redacted": redact_phi(sample),
    }


def medical_guardrails() -> dict[str, Any]:
    ensure_intelligent_healthcare()
    return {
        "report": "medical_guardrails",
        "guardrails": GOVERNANCE_POLICY,
        "blocked_patterns": list(BLOCKED_PATTERNS),
        "enforcement": "AISafetyPolicy",
    }


def clinical_recommendation_engine() -> dict[str, Any]:
    ensure_intelligent_healthcare()
    pack_count = ClinicalGuidelinePack.query.count()
    return _advisory(
        {
            "recommendation_type": "advisory",
            "rule_packs": pack_count,
            "human_review_required": True,
        },
        report="clinical_recommendation_engine",
        task_type="interpretation",
    )


def ai_monitoring_dashboard() -> dict[str, Any]:
    ensure_intelligent_healthcare()
    usage = AIUsageMetricsService.summary()
    ops = ai_usage_metrics()
    return {
        "report": "ai_monitoring_dashboard",
        "usage": usage,
        "operations": ops,
        "legacy_route": "/ai-operations",
    }


def dashboard_payload() -> dict[str, Any]:
    ensure_intelligent_healthcare()
    providers = AIProviderRegistry.list_providers()
    prompts = PromptRegistry.list_prompts()
    audit = AIAuditService.list_entries(page_size=5)
    usage = AIUsageMetricsService.summary()
    return {
        "platform": "Intelligent Healthcare Platform",
        "phase": "8",
        "sprint": "Intelligent Healthcare Platform",
        "status": "OK",
        "policy": GOVERNANCE_POLICY,
        "generated_at": datetime.utcnow().isoformat(),
        "summary": {
            "modules": len(FEATURES),
            "providers": providers.get("count", 0),
            "prompts": prompts.get("count", 0),
            "audit_entries": audit.get("count", 0),
            "usage_records": usage.get("count", 0),
            "scaffold_modules": 2,
        },
        "features": list(FEATURES),
    }


def intelligent_healthcare_readiness_report() -> dict[str, Any]:
    d = dashboard_payload()
    sections = {
        "ai_clinical_platform": ai_clinical_platform(),
        "medical_knowledge_base": medical_knowledge_base(),
        "clinical_rules_engine": clinical_rules_engine(),
        "reference_range_engine": reference_range_engine(),
        "loinc_registry": loinc_registry(),
        "icd10_registry": icd10_registry(),
        "snomed_mapping_layer": snomed_mapping_layer(),
        "drug_knowledge_layer": drug_knowledge_layer(),
        "medical_ocr_platform": medical_ocr_platform(),
        "voice_clinical_platform": voice_clinical_platform(),
        "ai_gateway": ai_gateway(),
        "ai_safety_layer": ai_safety_layer(),
        "phi_redaction": phi_redaction(),
        "medical_guardrails": medical_guardrails(),
        "ai_monitoring_dashboard": ai_monitoring_dashboard(),
    }
    return {
        "generated_at": datetime.utcnow().isoformat(),
        "phase": "8",
        "platform": d["platform"],
        "status": d["status"],
        "policy": GOVERNANCE_POLICY,
        "summary": d["summary"],
        "features": list(FEATURES),
        "sections": sections,
        "architecture_docs": [
            "docs/architecture/AI_ARCHITECTURE.md",
            "docs/architecture/AI_SEQUENCE_DIAGRAMS.md",
            "docs/architecture/AI_COMPONENTS.md",
            "docs/MEDICAL_AI_GUIDE.md",
        ],
        "legacy_hubs": ["/ai-clinical", "/ai-copilot", "/ai-operations", "/voice-platform", "/standards-advanced"],
    }


def intelligent_healthcare_governance_report() -> dict[str, Any]:
    return {
        "generated_at": datetime.utcnow().isoformat(),
        "phase": "8",
        "platform": "Intelligent Healthcare Platform",
        "governance": GOVERNANCE_POLICY,
        "safety_layer": ai_safety_layer(),
        "medical_guardrails": medical_guardrails(),
        "phi_redaction": phi_redaction(),
        "hallucination_detection": hallucination_detection(),
        "human_review_mandatory": True,
        "automatic_diagnosis_permitted": False,
        "audit_trail": prompt_audit(),
        "compliance_notes": [
            "All AI outputs are advisory-only",
            "Doctor review required before clinical action",
            "PHI redacted before external LLM calls",
            "Prompt and inference audit logged",
            "Blocked patterns prevent auto-diagnosis language",
        ],
    }
