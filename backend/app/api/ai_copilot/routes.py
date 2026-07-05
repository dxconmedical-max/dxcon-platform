"""AI Copilot Platform API routes — Phase 7.3."""

from __future__ import annotations

from flask import Blueprint

from app.services.ai_copilot_service import (
    dashboard_payload,
    reception_copilot,
    doctor_copilot,
    collector_copilot,
    lab_copilot,
    ceo_copilot,
    prompt_registry_view,
    prompt_version_view,
    conversation_audit,
    safety_layer,
    phi_redaction_demo,
    ai_routing,
    ai_copilot_readiness_report,
)

ai_copilot_bp = Blueprint("ai_copilot_api", __name__, url_prefix="/api/v1/ai-copilot")

@ai_copilot_bp.route("/dashboard", methods=["GET"])
def ai_copilot_dashboard_api():
    return dashboard_payload()

@ai_copilot_bp.route("/reception-copilot", methods=["GET"])
def ai_copilot_reception_copilot_api():
    return reception_copilot()

@ai_copilot_bp.route("/doctor-copilot", methods=["GET"])
def ai_copilot_doctor_copilot_api():
    return doctor_copilot()

@ai_copilot_bp.route("/collector-copilot", methods=["GET"])
def ai_copilot_collector_copilot_api():
    return collector_copilot()

@ai_copilot_bp.route("/lab-copilot", methods=["GET"])
def ai_copilot_lab_copilot_api():
    return lab_copilot()

@ai_copilot_bp.route("/ceo-copilot", methods=["GET"])
def ai_copilot_ceo_copilot_api():
    return ceo_copilot()

@ai_copilot_bp.route("/prompts", methods=["GET"])
def ai_copilot_prompt_registry_view_api():
    return prompt_registry_view()

@ai_copilot_bp.route("/prompt-versions", methods=["GET"])
def ai_copilot_prompt_version_view_api():
    return prompt_version_view()

@ai_copilot_bp.route("/audit", methods=["GET"])
def ai_copilot_conversation_audit_api():
    return conversation_audit()

@ai_copilot_bp.route("/safety", methods=["GET"])
def ai_copilot_safety_layer_api():
    return safety_layer()

@ai_copilot_bp.route("/phi-redaction", methods=["GET"])
def ai_copilot_phi_redaction_demo_api():
    return phi_redaction_demo()

@ai_copilot_bp.route("/routing", methods=["GET"])
def ai_copilot_ai_routing_api():
    return ai_routing()

@ai_copilot_bp.route("/readiness", methods=["GET"])
def ai_copilot_readiness_api():
    return ai_copilot_readiness_report()
