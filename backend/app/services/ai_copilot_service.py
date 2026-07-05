"""AI Copilot Platform business logic for Phase 7.3."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from app.ai_platform.audit import AIAuditService
from app.ai_platform.metrics import AIUsageMetricsService
from app.ai_platform.phi_redaction import redact_phi
from app.ai_platform.prompt_registry import PromptRegistry
from app.ai_platform.router import ModelRouter
from app.ai_platform.safety import AISafetyPolicy, CLINICAL_DISCLAIMER, BLOCKED_PATTERNS

AI_COPILOT_ROLES = ("SUPER_ADMIN", "ADMIN", "DOCTOR", "RECEPTION")

FEATURES = (
    "Reception Copilot",
    "Doctor Copilot",
    "Collector Copilot",
    "Lab Copilot",
    "CEO Copilot",
    "Prompt Registry",
    "Prompt Version",
    "Conversation Audit",
    "Safety Layer",
    "PHI Redaction",
    "AI Routing",
)

COPILOT_CONFIG = {
    "reception": {"route": "/reception", "api": "/api/v1/reception/dashboard", "role": "RECEPTION"},
    "doctor": {"route": "/doctor-portal", "api": "/api/v1/doctor/dashboard", "role": "DOCTOR"},
    "collector": {"route": "/collector", "api": "/api/v1/collector/jobs", "role": "COLLECTOR"},
    "lab": {"route": "/lab-operations", "api": "/api/v1/lab/dashboard", "role": "LAB"},
    "ceo": {"route": "/executive-metrics", "api": "/api/v1/executive-metrics/dashboard", "role": "SUPER_ADMIN"},
}


def ensure_ai_copilot() -> dict[str, Any]:
    PromptRegistry.ensure_defaults()
    return {"ready": True, "advisory_only": True}


def _copilot(name: str, description: str) -> dict[str, Any]:
    cfg = COPILOT_CONFIG[name]
    return {
        "copilot": name,
        "description": description,
        "advisory_only": True,
        "human_review_required": True,
        "web_route": cfg["route"],
        "api_route": cfg["api"],
        "target_role": cfg["role"],
        "status": "READY",
    }


def reception_copilot() -> dict[str, Any]:
    ensure_ai_copilot()
    return {"report": "reception_copilot", **_copilot("reception", "Patient registration and queue assistance")}


def doctor_copilot() -> dict[str, Any]:
    ensure_ai_copilot()
    return {"report": "doctor_copilot", **_copilot("doctor", "Result review and clinical summary assistance")}


def collector_copilot() -> dict[str, Any]:
    ensure_ai_copilot()
    return {"report": "collector_copilot", **_copilot("collector", "Collection route and shipment guidance")}


def lab_copilot() -> dict[str, Any]:
    ensure_ai_copilot()
    return {"report": "lab_copilot", **_copilot("lab", "Accession and TAT workflow assistance")}


def ceo_copilot() -> dict[str, Any]:
    ensure_ai_copilot()
    return {"report": "ceo_copilot", **_copilot("ceo", "Executive KPI narrative and forecast insights")}


def prompt_registry_view() -> dict[str, Any]:
    ensure_ai_copilot()
    data = PromptRegistry.list_prompts()
    data["report"] = "prompt_registry"
    return data


def prompt_version_view() -> dict[str, Any]:
    ensure_ai_copilot()
    prompts = PromptRegistry.list_prompts()
    versions = []
    for item in prompts.get("prompts", []):
        versions.append({"prompt_code": item.get("prompt_code"), "active_version": item.get("active_version")})
    return {"report": "prompt_version", "count": len(versions), "versions": versions}


def conversation_audit(limit: int = 50) -> dict[str, Any]:
    ensure_ai_copilot()
    records = AIAuditService.list_entries(page_size=limit)
    return {"report": "conversation_audit", **records}


def safety_layer() -> dict[str, Any]:
    ensure_ai_copilot()
    sample = AISafetyPolicy.check_request("interpretation", {"note": "advisory summary only"})
    return {
        "report": "safety_layer",
        "advisory_only": True,
        "disclaimer": CLINICAL_DISCLAIMER,
        "blocked_patterns": list(BLOCKED_PATTERNS),
        "sample_check": sample,
    }


def phi_redaction_demo(text: str = "Patient John Doe MRN-12345 result glucose 120") -> dict[str, Any]:
    ensure_ai_copilot()
    redacted = redact_phi(text)
    return {"report": "phi_redaction", "original_length": len(text), "redacted": redacted}


def ai_routing() -> dict[str, Any]:
    ensure_ai_copilot()
    from app.ai_platform.registry import AIProviderRegistry

    routes = {task: ModelRouter.resolve(task) for task in ModelRouter.DEFAULT_ROUTES}
    metrics = AIUsageMetricsService.summary()
    return {
        "report": "ai_routing",
        "default_routes": routes,
        "provider_types": AIProviderRegistry.list_types(),
        "usage": metrics,
    }


def ai_copilot_dashboard() -> dict[str, Any]:
    ensure_ai_copilot()
    prompts = PromptRegistry.list_prompts()
    audit = conversation_audit(limit=10)
    return {
        "report": "ai_copilot_dashboard",
        "status": "OK",
        "copilots_ready": 5,
        "prompts_total": prompts.get("count", 0),
        "audit_records": audit.get("count", 0),
    }


def dashboard_payload() -> dict[str, Any]:
    ensure_ai_copilot()
    dash = ai_copilot_dashboard()
    return {
        "platform": "AI Copilot Platform",
        "phase": "7.3",
        "sprint": "AI Copilot",
        "status": dash["status"],
        "advisory_only": True,
        "generated_at": datetime.utcnow().isoformat(),
        "summary": {
            "copilots_ready": dash["copilots_ready"],
            "prompts_total": dash["prompts_total"],
            "audit_records": dash["audit_records"],
        },
        "features": list(FEATURES),
    }


def ai_copilot_readiness_report() -> dict[str, Any]:
    d = dashboard_payload()
    return {
        "generated_at": datetime.utcnow().isoformat(),
        "phase": "7.3",
        "platform": d["platform"],
        "status": d["status"],
        "summary": d["summary"],
        "features": list(FEATURES),
        "sections": {
            "reception_copilot": reception_copilot(),
            "doctor_copilot": doctor_copilot(),
            "collector_copilot": collector_copilot(),
            "lab_copilot": lab_copilot(),
            "ceo_copilot": ceo_copilot(),
            "prompt_registry": prompt_registry_view(),
            "prompt_version": prompt_version_view(),
            "conversation_audit": conversation_audit(),
            "safety_layer": safety_layer(),
            "phi_redaction": phi_redaction_demo(),
            "ai_routing": ai_routing(),
        },
        "legacy_routes": ["/ai-clinical", "/ai-operations", "/api/v1/ai-platform"],
        "architecture_doc": "docs/architecture/AI_PLATFORM_ARCHITECTURE.md",
    }
