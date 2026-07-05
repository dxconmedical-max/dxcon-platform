"""Executive Metrics API routes — Phase 5 Sprint 5.9."""

from __future__ import annotations

from flask import Blueprint, request

from app.services.executive_metrics_service import (
    clinic_ranking,
    collector_sla_metrics,
    dashboard_payload,
    doctor_ranking,
    executive_metrics_readiness_report,
    growth_metrics,
    lab_sla_metrics,
    orders_metrics,
    revenue_forecast,
    revenue_metrics,
    tat_metrics,
)

executive_metrics_bp = Blueprint(
    "executive_metrics_api",
    __name__,
    url_prefix="/api/v1/executive-metrics",
)


def _dates():
    return request.args.get("date_from"), request.args.get("date_to")


@executive_metrics_bp.route("/dashboard", methods=["GET"])
def executive_metrics_dashboard_api():
    date_from, date_to = _dates()
    return dashboard_payload(date_from, date_to)


@executive_metrics_bp.route("/revenue", methods=["GET"])
def executive_metrics_revenue_api():
    date_from, date_to = _dates()
    return revenue_metrics(date_from, date_to)


@executive_metrics_bp.route("/tat", methods=["GET"])
def executive_metrics_tat_api():
    date_from, date_to = _dates()
    return tat_metrics(date_from, date_to)


@executive_metrics_bp.route("/orders", methods=["GET"])
def executive_metrics_orders_api():
    date_from, date_to = _dates()
    return orders_metrics(date_from, date_to)


@executive_metrics_bp.route("/growth", methods=["GET"])
def executive_metrics_growth_api():
    date_from, date_to = _dates()
    return growth_metrics(date_from, date_to)


@executive_metrics_bp.route("/lab-sla", methods=["GET"])
def executive_metrics_lab_sla_api():
    date_from, date_to = _dates()
    return lab_sla_metrics(date_from, date_to)


@executive_metrics_bp.route("/collector-sla", methods=["GET"])
def executive_metrics_collector_sla_api():
    date_from, date_to = _dates()
    return collector_sla_metrics(date_from, date_to)


@executive_metrics_bp.route("/clinic-ranking", methods=["GET"])
def executive_metrics_clinic_ranking_api():
    date_from, date_to = _dates()
    return clinic_ranking(date_from, date_to)


@executive_metrics_bp.route("/doctor-ranking", methods=["GET"])
def executive_metrics_doctor_ranking_api():
    date_from, date_to = _dates()
    return doctor_ranking(date_from, date_to)


@executive_metrics_bp.route("/revenue-forecast", methods=["GET"])
def executive_metrics_revenue_forecast_api():
    date_from, date_to = _dates()
    return revenue_forecast(date_from, date_to)


@executive_metrics_bp.route("/readiness", methods=["GET"])
def executive_metrics_readiness_api():
    return executive_metrics_readiness_report()
