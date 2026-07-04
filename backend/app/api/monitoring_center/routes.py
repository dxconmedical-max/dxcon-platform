"""Monitoring Center API routes — Phase 5 Sprint 5.2."""

from __future__ import annotations

from flask import Blueprint, request

from app.services.monitoring_center_service import (
    alerts_overview,
    api_latency_metrics,
    application_health,
    background_jobs_status,
    business_kpi_snapshot,
    dashboard_payload,
    database_health,
    error_rate_metrics,
    monitoring_readiness_report,
    queue_health,
    redis_health,
)

monitoring_center_bp = Blueprint(
    "monitoring_center_api",
    __name__,
    url_prefix="/api/v1/monitoring-center",
)


@monitoring_center_bp.route("/dashboard", methods=["GET"])
def monitoring_center_dashboard_api():
    return dashboard_payload()


@monitoring_center_bp.route("/application", methods=["GET"])
def monitoring_center_application_api():
    return application_health()


@monitoring_center_bp.route("/queues", methods=["GET"])
def monitoring_center_queues_api():
    return queue_health()


@monitoring_center_bp.route("/database", methods=["GET"])
def monitoring_center_database_api():
    return database_health()


@monitoring_center_bp.route("/redis", methods=["GET"])
def monitoring_center_redis_api():
    return redis_health()


@monitoring_center_bp.route("/latency", methods=["GET"])
def monitoring_center_latency_api():
    return api_latency_metrics()


@monitoring_center_bp.route("/errors", methods=["GET"])
def monitoring_center_errors_api():
    return error_rate_metrics()


@monitoring_center_bp.route("/jobs", methods=["GET"])
def monitoring_center_jobs_api():
    return background_jobs_status()


@monitoring_center_bp.route("/kpi", methods=["GET"])
def monitoring_center_kpi_api():
    return business_kpi_snapshot()


@monitoring_center_bp.route("/alerts", methods=["GET"])
def monitoring_center_alerts_api():
    limit = int(request.args.get("limit") or 50)
    return alerts_overview(limit=limit)


@monitoring_center_bp.route("/readiness", methods=["GET"])
def monitoring_center_readiness_api():
    return monitoring_readiness_report()
