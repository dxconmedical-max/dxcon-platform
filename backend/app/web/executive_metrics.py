"""Executive Metrics web routes — Phase 5 Sprint 5.9."""

from __future__ import annotations

from flask import Blueprint

from app.services.executive_metrics_service import EXECUTIVE_METRICS_ROLES
from app.utils.auth import role_required
from app.web.executive_metrics_lib import (
    build_clinic_ranking_body,
    build_collector_sla_body,
    build_dashboard_body,
    build_doctor_ranking_body,
    build_growth_body,
    build_lab_sla_body,
    build_orders_body,
    build_revenue_body,
    build_revenue_forecast_body,
    build_tat_body,
    render_metrics_page,
)

executive_metrics_web_bp = Blueprint("executive_metrics_web", __name__)


@executive_metrics_web_bp.route("/executive-metrics")
@role_required(*EXECUTIVE_METRICS_ROLES)
def executive_metrics_dashboard():
    return render_metrics_page("Executive Metrics", build_dashboard_body())


@executive_metrics_web_bp.route("/executive-metrics/revenue")
@role_required(*EXECUTIVE_METRICS_ROLES)
def executive_metrics_revenue():
    return render_metrics_page("Revenue", build_revenue_body())


@executive_metrics_web_bp.route("/executive-metrics/tat")
@role_required(*EXECUTIVE_METRICS_ROLES)
def executive_metrics_tat():
    return render_metrics_page("TAT", build_tat_body())


@executive_metrics_web_bp.route("/executive-metrics/orders")
@role_required(*EXECUTIVE_METRICS_ROLES)
def executive_metrics_orders():
    return render_metrics_page("Orders", build_orders_body())


@executive_metrics_web_bp.route("/executive-metrics/growth")
@role_required(*EXECUTIVE_METRICS_ROLES)
def executive_metrics_growth():
    return render_metrics_page("Growth", build_growth_body())


@executive_metrics_web_bp.route("/executive-metrics/lab-sla")
@role_required(*EXECUTIVE_METRICS_ROLES)
def executive_metrics_lab_sla():
    return render_metrics_page("Lab SLA", build_lab_sla_body())


@executive_metrics_web_bp.route("/executive-metrics/collector-sla")
@role_required(*EXECUTIVE_METRICS_ROLES)
def executive_metrics_collector_sla():
    return render_metrics_page("Collector SLA", build_collector_sla_body())


@executive_metrics_web_bp.route("/executive-metrics/clinic-ranking")
@role_required(*EXECUTIVE_METRICS_ROLES)
def executive_metrics_clinic_ranking():
    return render_metrics_page("Clinic Ranking", build_clinic_ranking_body())


@executive_metrics_web_bp.route("/executive-metrics/doctor-ranking")
@role_required(*EXECUTIVE_METRICS_ROLES)
def executive_metrics_doctor_ranking():
    return render_metrics_page("Doctor Ranking", build_doctor_ranking_body())


@executive_metrics_web_bp.route("/executive-metrics/revenue-forecast")
@role_required(*EXECUTIVE_METRICS_ROLES)
def executive_metrics_revenue_forecast():
    return render_metrics_page("Revenue Forecast", build_revenue_forecast_body())
