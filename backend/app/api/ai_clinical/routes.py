"""AI Clinical Platform API routes — Phase 4 Sprint 4.2."""

from __future__ import annotations

from flask import Blueprint, request, session

from app.services.ai_clinical_service import (
    AIClinicalError,
    clinical_summary,
    dashboard_payload,
    delta_check,
    detect_critical_values,
    doctor_review_flag,
    explain_reference_range,
    interpret_results,
    list_audit,
    list_prompts,
    list_providers,
    model_router_payload,
    patient_friendly_explanation,
    phi_redaction_demo,
    safety_disclaimer,
    usage_metrics,
)

ai_clinical_bp = Blueprint("ai_clinical_api", __name__, url_prefix="/api/v1/ai-clinical")


def _actor() -> str | None:
    return session.get("email")


@ai_clinical_bp.route("/dashboard", methods=["GET"])
def ai_clinical_dashboard_api():
    return dashboard_payload()


@ai_clinical_bp.route("/providers", methods=["GET"])
def ai_clinical_providers_api():
    return list_providers()


@ai_clinical_bp.route("/prompts", methods=["GET"])
def ai_clinical_prompts_api():
    return list_prompts()


@ai_clinical_bp.route("/router", methods=["GET"])
def ai_clinical_router_api():
    return model_router_payload(request.args.get("task_type"))


@ai_clinical_bp.route("/interpret", methods=["POST"])
def ai_clinical_interpret_api():
    data = request.get_json(silent=True) or {}
    try:
        return interpret_results(data, actor=_actor())
    except AIClinicalError as exc:
        return {"error": exc.message}, exc.status_code


@ai_clinical_bp.route("/critical-detect", methods=["POST"])
def ai_clinical_critical_api():
    data = request.get_json(silent=True) or {}
    try:
        return detect_critical_values(data, actor=_actor())
    except AIClinicalError as exc:
        return {"error": exc.message}, exc.status_code


@ai_clinical_bp.route("/delta-check", methods=["POST"])
def ai_clinical_delta_api():
    data = request.get_json(silent=True) or {}
    try:
        return delta_check(data, actor=_actor())
    except AIClinicalError as exc:
        return {"error": exc.message}, exc.status_code


@ai_clinical_bp.route("/reference-ranges/explain", methods=["POST"])
def ai_clinical_reference_api():
    data = request.get_json(silent=True) or {}
    try:
        return explain_reference_range(data, actor=_actor())
    except AIClinicalError as exc:
        return {"error": exc.message}, exc.status_code


@ai_clinical_bp.route("/clinical-summary", methods=["POST"])
def ai_clinical_summary_api():
    data = request.get_json(silent=True) or {}
    try:
        return clinical_summary(data, actor=_actor())
    except AIClinicalError as exc:
        return {"error": exc.message}, exc.status_code


@ai_clinical_bp.route("/patient-friendly", methods=["POST"])
def ai_clinical_patient_friendly_api():
    data = request.get_json(silent=True) or {}
    try:
        return patient_friendly_explanation(data, actor=_actor())
    except AIClinicalError as exc:
        return {"error": exc.message}, exc.status_code


@ai_clinical_bp.route("/doctor-review-flag", methods=["GET"])
def ai_clinical_review_flag_api():
    pending = request.args.get("pending_results", "").lower() in {"1", "true", "yes"}
    return doctor_review_flag({"pending_results": pending})


@ai_clinical_bp.route("/audit", methods=["GET"])
def ai_clinical_audit_api():
    page = request.args.get("page", 1)
    page_size = request.args.get("page_size", 50)
    return list_audit(page=page, page_size=page_size)


@ai_clinical_bp.route("/usage", methods=["GET"])
def ai_clinical_usage_api():
    return usage_metrics()


@ai_clinical_bp.route("/safety/disclaimer", methods=["GET"])
def ai_clinical_disclaimer_api():
    return safety_disclaimer()


@ai_clinical_bp.route("/safety/redact", methods=["POST"])
def ai_clinical_redact_api():
    data = request.get_json(silent=True) or {}
    text = data.get("text") or data.get("sample_text") or ""
    return phi_redaction_demo(text, actor=_actor())
