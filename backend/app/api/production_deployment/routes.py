"""Production Deployment API routes — Phase 5 Sprint 5.5."""

from __future__ import annotations

from flask import Blueprint

from app.services.production_deployment_service import (
    dashboard_payload,
    docker_production_profile,
    health_probes,
    nginx_production,
    production_deployment_dashboard,
    production_deployment_readiness_report,
    release_checklist,
    rollback_checklist,
    rolling_deployment,
    zero_downtime_migration,
)

production_deployment_bp = Blueprint(
    "production_deployment_api",
    __name__,
    url_prefix="/api/v1/production-deployment",
)


@production_deployment_bp.route("/dashboard", methods=["GET"])
def production_deployment_dashboard_api():
    return dashboard_payload()


@production_deployment_bp.route("/docker", methods=["GET"])
def production_deployment_docker_api():
    return docker_production_profile()


@production_deployment_bp.route("/nginx", methods=["GET"])
def production_deployment_nginx_api():
    return nginx_production()


@production_deployment_bp.route("/probes", methods=["GET"])
def production_deployment_probes_api():
    return health_probes()


@production_deployment_bp.route("/rolling", methods=["GET"])
def production_deployment_rolling_api():
    return rolling_deployment()


@production_deployment_bp.route("/migration", methods=["GET"])
def production_deployment_migration_api():
    return zero_downtime_migration()


@production_deployment_bp.route("/release", methods=["GET"])
def production_deployment_release_api():
    return release_checklist()


@production_deployment_bp.route("/rollback", methods=["GET"])
def production_deployment_rollback_api():
    return rollback_checklist()


@production_deployment_bp.route("/inventory", methods=["GET"])
def production_deployment_inventory_api():
    return production_deployment_dashboard()


@production_deployment_bp.route("/readiness", methods=["GET"])
def production_deployment_readiness_api():
    return production_deployment_readiness_report()
