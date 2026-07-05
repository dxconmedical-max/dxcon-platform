"""AI Operations API routes — Phase 5 Sprint 5.10."""

from __future__ import annotations

from flask import Blueprint, request

from app.services.ai_operations_service import (
    ai_accuracy_metrics,
    ai_cost_metrics,
    ai_incident_summary,
    ai_operations_readiness_report,
    ai_usage_metrics,
    dashboard_payload,
    model_health_metrics,
    prompt_version_metrics,
)

ai_operations_bp = Blueprint(
    "ai_operations_api",
    __name__,
    url_prefix="/api/v1/ai-operations",
)


def _dates():
    return request.args.get("date_from"), request.args.get("date_to")


@ai_operations_bp.route("/dashboard", methods=["GET"])
def ai_operations_dashboard_api():
    date_from, date_to = _dates()
    return dashboard_payload(date_from, date_to)


@ai_operations_bp.route("/incident-summary", methods=["GET"])
def ai_operations_incident_summary_api():
    date_from, date_to = _dates()
    return ai_incident_summary(date_from, date_to)


@ai_operations_bp.route("/usage", methods=["GET"])
def ai_operations_usage_api():
    date_from, date_to = _dates()
    return ai_usage_metrics(date_from, date_to)


@ai_operations_bp.route("/cost", methods=["GET"])
def ai_operations_cost_api():
    date_from, date_to = _dates()
    return ai_cost_metrics(date_from, date_to)


@ai_operations_bp.route("/accuracy", methods=["GET"])
def ai_operations_accuracy_api():
    date_from, date_to = _dates()
    return ai_accuracy_metrics(date_from, date_to)


@ai_operations_bp.route("/model-health", methods=["GET"])
def ai_operations_model_health_api():
    date_from, date_to = _dates()
    return model_health_metrics(date_from, date_to)


@ai_operations_bp.route("/prompt-version", methods=["GET"])
def ai_operations_prompt_version_api():
    return prompt_version_metrics()


@ai_operations_bp.route("/readiness", methods=["GET"])
def ai_operations_readiness_api():
    return ai_operations_readiness_report()
