"""Monitoring Center web routes — Phase 5 Sprint 5.2."""

from __future__ import annotations

from flask import Blueprint

from app.services.monitoring_center_service import MONITORING_ROLES
from app.utils.auth import role_required
from app.web.monitoring_center_lib import (
    build_alerts_body,
    build_application_body,
    build_dashboard_body,
    build_database_body,
    build_errors_body,
    build_jobs_body,
    build_kpi_body,
    build_latency_body,
    build_queues_body,
    build_redis_body,
    render_monitoring_page,
)

monitoring_center_web_bp = Blueprint("monitoring_center_web", __name__)


@monitoring_center_web_bp.route("/monitoring")
@role_required(*MONITORING_ROLES)
def monitoring_center_dashboard():
    return render_monitoring_page("Monitoring Center", build_dashboard_body())


@monitoring_center_web_bp.route("/monitoring/application")
@role_required(*MONITORING_ROLES)
def monitoring_center_application():
    return render_monitoring_page("Application Health", build_application_body())


@monitoring_center_web_bp.route("/monitoring/queues")
@role_required(*MONITORING_ROLES)
def monitoring_center_queues():
    return render_monitoring_page("Queue Health", build_queues_body())


@monitoring_center_web_bp.route("/monitoring/database")
@role_required(*MONITORING_ROLES)
def monitoring_center_database():
    return render_monitoring_page("Database Health", build_database_body())


@monitoring_center_web_bp.route("/monitoring/redis")
@role_required(*MONITORING_ROLES)
def monitoring_center_redis():
    return render_monitoring_page("Redis Health", build_redis_body())


@monitoring_center_web_bp.route("/monitoring/latency")
@role_required(*MONITORING_ROLES)
def monitoring_center_latency():
    return render_monitoring_page("API Latency", build_latency_body())


@monitoring_center_web_bp.route("/monitoring/errors")
@role_required(*MONITORING_ROLES)
def monitoring_center_errors():
    return render_monitoring_page("Error Rate", build_errors_body())


@monitoring_center_web_bp.route("/monitoring/jobs")
@role_required(*MONITORING_ROLES)
def monitoring_center_jobs():
    return render_monitoring_page("Background Jobs", build_jobs_body())


@monitoring_center_web_bp.route("/monitoring/kpi")
@role_required(*MONITORING_ROLES)
def monitoring_center_kpi():
    return render_monitoring_page("Business KPI", build_kpi_body())


@monitoring_center_web_bp.route("/monitoring/alerts")
@role_required(*MONITORING_ROLES)
def monitoring_center_alerts():
    return render_monitoring_page("Alerts", build_alerts_body())
