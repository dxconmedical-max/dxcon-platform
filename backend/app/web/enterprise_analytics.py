"""Enterprise Analytics web routes — Phase 4 Sprint 4.6."""

from __future__ import annotations

from flask import Blueprint

from app.services.enterprise_analytics_service import ANALYTICS_ROLES
from app.utils.auth import role_required
from app.web.enterprise_analytics_lib import (
    build_ai_body,
    build_collectors_body,
    build_critical_body,
    build_dashboard_body,
    build_export_body,
    build_integrations_body,
    build_lab_sla_body,
    build_partners_body,
    build_rejections_body,
    build_revenue_body,
    build_tat_body,
    render_analytics_page,
)

enterprise_analytics_web_bp = Blueprint("enterprise_analytics_web", __name__)


@enterprise_analytics_web_bp.route("/enterprise-analytics")
@role_required(*ANALYTICS_ROLES)
def enterprise_analytics_dashboard():
    return render_analytics_page("Enterprise Analytics", build_dashboard_body())


@enterprise_analytics_web_bp.route("/enterprise-analytics/revenue")
@role_required(*ANALYTICS_ROLES)
def enterprise_analytics_revenue():
    return render_analytics_page("Revenue Analytics", build_revenue_body())


@enterprise_analytics_web_bp.route("/enterprise-analytics/lab-sla")
@role_required(*ANALYTICS_ROLES)
def enterprise_analytics_lab_sla():
    return render_analytics_page("Lab SLA Analytics", build_lab_sla_body())


@enterprise_analytics_web_bp.route("/enterprise-analytics/collectors")
@role_required(*ANALYTICS_ROLES)
def enterprise_analytics_collectors():
    return render_analytics_page("Collector SLA Analytics", build_collectors_body())


@enterprise_analytics_web_bp.route("/enterprise-analytics/partners")
@role_required(*ANALYTICS_ROLES)
def enterprise_analytics_partners():
    return render_analytics_page("Partner Performance", build_partners_body())


@enterprise_analytics_web_bp.route("/enterprise-analytics/tat")
@role_required(*ANALYTICS_ROLES)
def enterprise_analytics_tat():
    return render_analytics_page("Turnaround Time Analytics", build_tat_body())


@enterprise_analytics_web_bp.route("/enterprise-analytics/rejections")
@role_required(*ANALYTICS_ROLES)
def enterprise_analytics_rejections():
    return render_analytics_page("Sample Rejection Analytics", build_rejections_body())


@enterprise_analytics_web_bp.route("/enterprise-analytics/critical")
@role_required(*ANALYTICS_ROLES)
def enterprise_analytics_critical():
    return render_analytics_page("Critical Result Analytics", build_critical_body())


@enterprise_analytics_web_bp.route("/enterprise-analytics/ai")
@role_required(*ANALYTICS_ROLES)
def enterprise_analytics_ai():
    return render_analytics_page("AI Usage Analytics", build_ai_body())


@enterprise_analytics_web_bp.route("/enterprise-analytics/integrations")
@role_required(*ANALYTICS_ROLES)
def enterprise_analytics_integrations():
    return render_analytics_page("Integration Failure Analytics", build_integrations_body())


@enterprise_analytics_web_bp.route("/enterprise-analytics/export")
@role_required(*ANALYTICS_ROLES)
def enterprise_analytics_export():
    return render_analytics_page("Executive KPI Export", build_export_body())
