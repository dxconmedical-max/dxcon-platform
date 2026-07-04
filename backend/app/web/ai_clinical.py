"""AI Clinical Platform web routes — Phase 4 Sprint 4.2."""

from __future__ import annotations

import json

from flask import Blueprint, request, session

from app.services.ai_clinical_service import AIClinicalError, CLINICAL_ROLES, phi_redaction_demo
from app.utils.auth import role_required
from app.web.ai_clinical_lib import (
    build_audit_body,
    build_critical_form_body,
    build_dashboard_body,
    build_delta_form_body,
    build_interpret_form_body,
    build_patient_friendly_form_body,
    build_prompts_body,
    build_providers_body,
    build_reference_form_body,
    build_review_flags_body,
    build_router_body,
    build_safety_body,
    build_summary_form_body,
    build_usage_body,
    render_clinical_page,
)
from app.services import ai_clinical_service as svc

ai_clinical_web_bp = Blueprint("ai_clinical_web", __name__)


def _actor() -> str | None:
    return session.get("email")


def _parse_payload() -> dict:
    raw = request.form.get("payload", "").strip()
    if not raw:
        return {}
    return json.loads(raw)


def _json_form_route(handler, builder):
    if request.method == "GET":
        return render_clinical_page(handler.__name__, builder())
    try:
        result = handler(_parse_payload(), actor=_actor())
        return render_clinical_page(handler.__name__, builder(result=result))
    except json.JSONDecodeError:
        return render_clinical_page(handler.__name__, builder(error="Invalid JSON payload."))
    except AIClinicalError as exc:
        return render_clinical_page(handler.__name__, builder(error=exc.message))


@ai_clinical_web_bp.route("/ai-clinical")
@role_required(*CLINICAL_ROLES)
def ai_clinical_dashboard():
    return render_clinical_page("AI Clinical Platform", build_dashboard_body())


@ai_clinical_web_bp.route("/ai-clinical/providers")
@role_required(*CLINICAL_ROLES)
def ai_clinical_providers():
    return render_clinical_page("AI Providers", build_providers_body())


@ai_clinical_web_bp.route("/ai-clinical/prompts")
@role_required(*CLINICAL_ROLES)
def ai_clinical_prompts():
    return render_clinical_page("Prompt Registry", build_prompts_body())


@ai_clinical_web_bp.route("/ai-clinical/router")
@role_required(*CLINICAL_ROLES)
def ai_clinical_router():
    return render_clinical_page("Model Router", build_router_body())


@ai_clinical_web_bp.route("/ai-clinical/audit")
@role_required(*CLINICAL_ROLES)
def ai_clinical_audit():
    return render_clinical_page("AI Audit Log", build_audit_body())


@ai_clinical_web_bp.route("/ai-clinical/usage")
@role_required(*CLINICAL_ROLES)
def ai_clinical_usage():
    return render_clinical_page("AI Usage Metrics", build_usage_body())


@ai_clinical_web_bp.route("/ai-clinical/review-flags")
@role_required(*CLINICAL_ROLES)
def ai_clinical_review_flags():
    return render_clinical_page("Doctor Review Flag", build_review_flags_body())


@ai_clinical_web_bp.route("/ai-clinical/safety", methods=["GET", "POST"])
@role_required(*CLINICAL_ROLES)
def ai_clinical_safety():
    if request.method == "GET":
        return render_clinical_page("Safety & PHI", build_safety_body())
    try:
        result = phi_redaction_demo(request.form.get("sample_text", ""), actor=_actor())
        return render_clinical_page("Safety & PHI", build_safety_body(result=result))
    except AIClinicalError as exc:
        return render_clinical_page("Safety & PHI", build_safety_body(error=exc.message))


@ai_clinical_web_bp.route("/ai-clinical/interpret", methods=["GET", "POST"])
@role_required(*CLINICAL_ROLES)
def ai_clinical_interpret():
    return _json_form_route(svc.interpret_results, build_interpret_form_body)


@ai_clinical_web_bp.route("/ai-clinical/critical", methods=["GET", "POST"])
@role_required(*CLINICAL_ROLES)
def ai_clinical_critical():
    return _json_form_route(svc.detect_critical_values, build_critical_form_body)


@ai_clinical_web_bp.route("/ai-clinical/delta", methods=["GET", "POST"])
@role_required(*CLINICAL_ROLES)
def ai_clinical_delta():
    return _json_form_route(svc.delta_check, build_delta_form_body)


@ai_clinical_web_bp.route("/ai-clinical/reference-ranges", methods=["GET", "POST"])
@role_required(*CLINICAL_ROLES)
def ai_clinical_reference_ranges():
    return _json_form_route(svc.explain_reference_range, build_reference_form_body)


@ai_clinical_web_bp.route("/ai-clinical/summary", methods=["GET", "POST"])
@role_required(*CLINICAL_ROLES)
def ai_clinical_summary():
    return _json_form_route(svc.clinical_summary, build_summary_form_body)


@ai_clinical_web_bp.route("/ai-clinical/patient-friendly", methods=["GET", "POST"])
@role_required(*CLINICAL_ROLES)
def ai_clinical_patient_friendly():
    return _json_form_route(svc.patient_friendly_explanation, build_patient_friendly_form_body)
