"""AI Copilot Platform web routes — Phase 7.3."""

from __future__ import annotations

from flask import Blueprint

from app.services.ai_copilot_service import AI_COPILOT_ROLES
from app.utils.auth import role_required
from app.web.ai_copilot_lib import (
    build_dashboard_body,
    build_reception_copilot_body,
    build_doctor_copilot_body,
    build_collector_copilot_body,
    build_lab_copilot_body,
    build_ceo_copilot_body,
    build_prompt_registry_view_body,
    build_prompt_version_view_body,
    build_conversation_audit_body,
    build_safety_layer_body,
    build_phi_redaction_demo_body,
    build_ai_routing_body,
    render_hub_page,
)

ai_copilot_web_bp = Blueprint("ai_copilot_web", __name__)

@ai_copilot_web_bp.route("/ai-copilot")
@role_required(*AI_COPILOT_ROLES)
def ai_copilot_dashboard():
    return render_hub_page("AI Copilot Platform", build_dashboard_body())
@ai_copilot_web_bp.route("/ai-copilot/reception-copilot")
@role_required(*AI_COPILOT_ROLES)
def ai_copilot_reception_copilot():
    return render_hub_page("Reception Copilot", build_reception_copilot_body())
@ai_copilot_web_bp.route("/ai-copilot/doctor-copilot")
@role_required(*AI_COPILOT_ROLES)
def ai_copilot_doctor_copilot():
    return render_hub_page("Doctor Copilot", build_doctor_copilot_body())
@ai_copilot_web_bp.route("/ai-copilot/collector-copilot")
@role_required(*AI_COPILOT_ROLES)
def ai_copilot_collector_copilot():
    return render_hub_page("Collector Copilot", build_collector_copilot_body())
@ai_copilot_web_bp.route("/ai-copilot/lab-copilot")
@role_required(*AI_COPILOT_ROLES)
def ai_copilot_lab_copilot():
    return render_hub_page("Lab Copilot", build_lab_copilot_body())
@ai_copilot_web_bp.route("/ai-copilot/ceo-copilot")
@role_required(*AI_COPILOT_ROLES)
def ai_copilot_ceo_copilot():
    return render_hub_page("CEO Copilot", build_ceo_copilot_body())
@ai_copilot_web_bp.route("/ai-copilot/prompts")
@role_required(*AI_COPILOT_ROLES)
def ai_copilot_prompt_registry_view():
    return render_hub_page("Prompt Registry", build_prompt_registry_view_body())
@ai_copilot_web_bp.route("/ai-copilot/prompt-versions")
@role_required(*AI_COPILOT_ROLES)
def ai_copilot_prompt_version_view():
    return render_hub_page("Prompt Version", build_prompt_version_view_body())
@ai_copilot_web_bp.route("/ai-copilot/audit")
@role_required(*AI_COPILOT_ROLES)
def ai_copilot_conversation_audit():
    return render_hub_page("Conversation Audit", build_conversation_audit_body())
@ai_copilot_web_bp.route("/ai-copilot/safety")
@role_required(*AI_COPILOT_ROLES)
def ai_copilot_safety_layer():
    return render_hub_page("Safety Layer", build_safety_layer_body())
@ai_copilot_web_bp.route("/ai-copilot/phi-redaction")
@role_required(*AI_COPILOT_ROLES)
def ai_copilot_phi_redaction_demo():
    return render_hub_page("PHI Redaction", build_phi_redaction_demo_body())
@ai_copilot_web_bp.route("/ai-copilot/routing")
@role_required(*AI_COPILOT_ROLES)
def ai_copilot_ai_routing():
    return render_hub_page("AI Routing", build_ai_routing_body())

