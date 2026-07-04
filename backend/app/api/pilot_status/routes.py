"""Pilot Status API routes — Phase 5 Sprint 5.6."""

from __future__ import annotations

from flask import Blueprint

from app.services.pilot_status_service import (
    active_clinics,
    active_labs,
    collectors_online,
    dashboard_payload,
    doctors_online,
    pilot_alerts,
    pilot_status_dashboard,
    pilot_status_overview,
    pilot_status_readiness_report,
    todays_orders,
    todays_revenue,
)

pilot_status_bp = Blueprint(
    "pilot_status_api",
    __name__,
    url_prefix="/api/v1/pilot-status",
)


@pilot_status_bp.route("/dashboard", methods=["GET"])
def pilot_status_dashboard_api():
    return dashboard_payload()


@pilot_status_bp.route("/overview", methods=["GET"])
def pilot_status_overview_api():
    return pilot_status_overview()


@pilot_status_bp.route("/clinics", methods=["GET"])
def pilot_status_clinics_api():
    return active_clinics()


@pilot_status_bp.route("/labs", methods=["GET"])
def pilot_status_labs_api():
    return active_labs()


@pilot_status_bp.route("/collectors", methods=["GET"])
def pilot_status_collectors_api():
    return collectors_online()


@pilot_status_bp.route("/doctors", methods=["GET"])
def pilot_status_doctors_api():
    return doctors_online()


@pilot_status_bp.route("/orders", methods=["GET"])
def pilot_status_orders_api():
    return todays_orders()


@pilot_status_bp.route("/revenue", methods=["GET"])
def pilot_status_revenue_api():
    return todays_revenue()


@pilot_status_bp.route("/alerts", methods=["GET"])
def pilot_status_alerts_api():
    return pilot_alerts()


@pilot_status_bp.route("/inventory", methods=["GET"])
def pilot_status_inventory_api():
    return pilot_status_dashboard()


@pilot_status_bp.route("/readiness", methods=["GET"])
def pilot_status_readiness_api():
    return pilot_status_readiness_report()
