"""Pilot Status web routes — Phase 5 Sprint 5.6."""

from __future__ import annotations

from flask import Blueprint

from app.services.pilot_status_service import PILOT_STATUS_ROLES
from app.utils.auth import role_required
from app.web.pilot_status_lib import (
    build_alerts_body,
    build_clinics_body,
    build_collectors_body,
    build_dashboard_body,
    build_doctors_body,
    build_labs_body,
    build_orders_body,
    build_revenue_body,
    render_pilot_status_page,
)

pilot_status_web_bp = Blueprint("pilot_status_web", __name__)


@pilot_status_web_bp.route("/pilot-status")
@role_required(*PILOT_STATUS_ROLES)
def pilot_status_dashboard():
    return render_pilot_status_page("Pilot Status", build_dashboard_body())


@pilot_status_web_bp.route("/pilot-status/clinics")
@role_required(*PILOT_STATUS_ROLES)
def pilot_status_clinics():
    return render_pilot_status_page("Active Clinics", build_clinics_body())


@pilot_status_web_bp.route("/pilot-status/labs")
@role_required(*PILOT_STATUS_ROLES)
def pilot_status_labs():
    return render_pilot_status_page("Active Labs", build_labs_body())


@pilot_status_web_bp.route("/pilot-status/collectors")
@role_required(*PILOT_STATUS_ROLES)
def pilot_status_collectors():
    return render_pilot_status_page("Collectors Online", build_collectors_body())


@pilot_status_web_bp.route("/pilot-status/doctors")
@role_required(*PILOT_STATUS_ROLES)
def pilot_status_doctors():
    return render_pilot_status_page("Doctors Online", build_doctors_body())


@pilot_status_web_bp.route("/pilot-status/orders")
@role_required(*PILOT_STATUS_ROLES)
def pilot_status_orders():
    return render_pilot_status_page("Today's Orders", build_orders_body())


@pilot_status_web_bp.route("/pilot-status/revenue")
@role_required(*PILOT_STATUS_ROLES)
def pilot_status_revenue():
    return render_pilot_status_page("Today's Revenue", build_revenue_body())


@pilot_status_web_bp.route("/pilot-status/alerts")
@role_required(*PILOT_STATUS_ROLES)
def pilot_status_alerts():
    return render_pilot_status_page("Alerts", build_alerts_body())
