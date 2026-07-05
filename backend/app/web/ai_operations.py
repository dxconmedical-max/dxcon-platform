"""AI Operations web routes — Phase 5 Sprint 5.10."""

from __future__ import annotations

from flask import Blueprint

from app.services.ai_operations_service import AI_OPERATIONS_ROLES
from app.utils.auth import role_required
from app.web.ai_operations_lib import (
    build_accuracy_body,
    build_cost_body,
    build_dashboard_body,
    build_incident_summary_body,
    build_model_health_body,
    build_prompt_version_body,
    build_usage_body,
    render_ai_ops_page,
)

ai_operations_web_bp = Blueprint("ai_operations_web", __name__)


@ai_operations_web_bp.route("/ai-operations")
@role_required(*AI_OPERATIONS_ROLES)
def ai_operations_dashboard():
    return render_ai_ops_page("AI Operations", build_dashboard_body())


@ai_operations_web_bp.route("/ai-operations/incident-summary")
@role_required(*AI_OPERATIONS_ROLES)
def ai_operations_incident_summary():
    return render_ai_ops_page("AI Incident Summary", build_incident_summary_body())


@ai_operations_web_bp.route("/ai-operations/usage")
@role_required(*AI_OPERATIONS_ROLES)
def ai_operations_usage():
    return render_ai_ops_page("AI Usage", build_usage_body())


@ai_operations_web_bp.route("/ai-operations/cost")
@role_required(*AI_OPERATIONS_ROLES)
def ai_operations_cost():
    return render_ai_ops_page("AI Cost", build_cost_body())


@ai_operations_web_bp.route("/ai-operations/accuracy")
@role_required(*AI_OPERATIONS_ROLES)
def ai_operations_accuracy():
    return render_ai_ops_page("AI Accuracy", build_accuracy_body())


@ai_operations_web_bp.route("/ai-operations/model-health")
@role_required(*AI_OPERATIONS_ROLES)
def ai_operations_model_health():
    return render_ai_ops_page("Model Health", build_model_health_body())


@ai_operations_web_bp.route("/ai-operations/prompt-version")
@role_required(*AI_OPERATIONS_ROLES)
def ai_operations_prompt_version():
    return render_ai_ops_page("Prompt Version", build_prompt_version_body())
