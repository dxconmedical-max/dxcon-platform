"""Enterprise Analytics API routes — Phase 4 Sprint 4.6."""

from __future__ import annotations

from flask import Blueprint, request

from app.services.enterprise_analytics_service import (
    ai_usage_analytics,
    collector_sla_analytics,
    critical_result_analytics,
    dashboard_payload,
    executive_kpi_export,
    integration_failure_analytics,
    lab_sla_analytics,
    partner_performance,
    revenue_analytics,
    sample_rejection_analytics,
    turnaround_time_analytics,
)

enterprise_analytics_bp = Blueprint(
    "enterprise_analytics_api",
    __name__,
    url_prefix="/api/v1/enterprise-analytics",
)


def _dates():
    return request.args.get("date_from"), request.args.get("date_to")


@enterprise_analytics_bp.route("/dashboard", methods=["GET"])
def enterprise_analytics_dashboard_api():
    date_from, date_to = _dates()
    return dashboard_payload(date_from, date_to)


@enterprise_analytics_bp.route("/revenue", methods=["GET"])
def enterprise_analytics_revenue_api():
    date_from, date_to = _dates()
    return revenue_analytics(date_from, date_to)


@enterprise_analytics_bp.route("/lab-sla", methods=["GET"])
def enterprise_analytics_lab_sla_api():
    date_from, date_to = _dates()
    return lab_sla_analytics(date_from, date_to)


@enterprise_analytics_bp.route("/collector-sla", methods=["GET"])
def enterprise_analytics_collector_sla_api():
    date_from, date_to = _dates()
    return collector_sla_analytics(date_from, date_to)


@enterprise_analytics_bp.route("/partners", methods=["GET"])
def enterprise_analytics_partners_api():
    date_from, date_to = _dates()
    return partner_performance(date_from, date_to)


@enterprise_analytics_bp.route("/turnaround-time", methods=["GET"])
def enterprise_analytics_tat_api():
    date_from, date_to = _dates()
    return turnaround_time_analytics(date_from, date_to)


@enterprise_analytics_bp.route("/rejections", methods=["GET"])
def enterprise_analytics_rejections_api():
    date_from, date_to = _dates()
    return sample_rejection_analytics(date_from, date_to)


@enterprise_analytics_bp.route("/critical-results", methods=["GET"])
def enterprise_analytics_critical_api():
    date_from, date_to = _dates()
    return critical_result_analytics(date_from, date_to)


@enterprise_analytics_bp.route("/ai-usage", methods=["GET"])
def enterprise_analytics_ai_api():
    date_from, date_to = _dates()
    return ai_usage_analytics(date_from, date_to)


@enterprise_analytics_bp.route("/integration-failures", methods=["GET"])
def enterprise_analytics_integrations_api():
    date_from, date_to = _dates()
    return integration_failure_analytics(date_from, date_to)


@enterprise_analytics_bp.route("/export", methods=["GET"])
def enterprise_analytics_export_api():
    date_from, date_to = _dates()
    export_format = request.args.get("format", "json")
    payload = executive_kpi_export(date_from, date_to, export_format=export_format)
    if export_format.lower() == "csv":
        return payload.get("csv", ""), 200, {"Content-Type": "text/csv; charset=utf-8"}
    return payload
