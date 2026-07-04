"""Production Deployment web routes — Phase 5 Sprint 5.5."""

from __future__ import annotations

from flask import Blueprint

from app.services.production_deployment_service import PRODUCTION_DEPLOYMENT_ROLES
from app.utils.auth import role_required
from app.web.production_deployment_lib import (
    build_dashboard_body,
    build_docker_body,
    build_migration_body,
    build_nginx_body,
    build_probes_body,
    build_release_body,
    build_rollback_body,
    build_rolling_body,
    render_deployment_page,
)

production_deployment_web_bp = Blueprint("production_deployment_web", __name__)


@production_deployment_web_bp.route("/production-deployment")
@role_required(*PRODUCTION_DEPLOYMENT_ROLES)
def production_deployment_dashboard():
    return render_deployment_page("Production Deployment", build_dashboard_body())


@production_deployment_web_bp.route("/production-deployment/docker")
@role_required(*PRODUCTION_DEPLOYMENT_ROLES)
def production_deployment_docker():
    return render_deployment_page("Docker Production Profile", build_docker_body())


@production_deployment_web_bp.route("/production-deployment/nginx")
@role_required(*PRODUCTION_DEPLOYMENT_ROLES)
def production_deployment_nginx():
    return render_deployment_page("Nginx Production", build_nginx_body())


@production_deployment_web_bp.route("/production-deployment/probes")
@role_required(*PRODUCTION_DEPLOYMENT_ROLES)
def production_deployment_probes():
    return render_deployment_page("Health Probes", build_probes_body())


@production_deployment_web_bp.route("/production-deployment/rolling")
@role_required(*PRODUCTION_DEPLOYMENT_ROLES)
def production_deployment_rolling():
    return render_deployment_page("Rolling Deployment", build_rolling_body())


@production_deployment_web_bp.route("/production-deployment/migration")
@role_required(*PRODUCTION_DEPLOYMENT_ROLES)
def production_deployment_migration():
    return render_deployment_page("Zero-downtime Migration", build_migration_body())


@production_deployment_web_bp.route("/production-deployment/release")
@role_required(*PRODUCTION_DEPLOYMENT_ROLES)
def production_deployment_release():
    return render_deployment_page("Release Checklist", build_release_body())


@production_deployment_web_bp.route("/production-deployment/rollback")
@role_required(*PRODUCTION_DEPLOYMENT_ROLES)
def production_deployment_rollback():
    return render_deployment_page("Rollback Checklist", build_rollback_body())
