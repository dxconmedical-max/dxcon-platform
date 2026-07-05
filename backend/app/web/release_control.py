"""Release Control web routes — Phase 5 Sprint 5.12."""

from __future__ import annotations

from flask import Blueprint

from app.services.release_control_service import RELEASE_CONTROL_ROLES
from app.utils.auth import role_required
from app.web.release_control_lib import (
    build_audit_body,
    build_dashboard_body,
    build_deployment_body,
    build_history_body,
    build_migration_body,
    build_rollback_body,
    build_version_compare_body,
    render_control_page,
)

release_control_web_bp = Blueprint("release_control_web", __name__)


@release_control_web_bp.route("/release-control")
@role_required(*RELEASE_CONTROL_ROLES)
def release_control_dashboard():
    return render_control_page("Release Control", build_dashboard_body())


@release_control_web_bp.route("/release-control/history")
@role_required(*RELEASE_CONTROL_ROLES)
def release_control_history():
    return render_control_page("Release History", build_history_body())


@release_control_web_bp.route("/release-control/version-compare")
@role_required(*RELEASE_CONTROL_ROLES)
def release_control_version_compare():
    return render_control_page("Version Compare", build_version_compare_body())


@release_control_web_bp.route("/release-control/migration")
@role_required(*RELEASE_CONTROL_ROLES)
def release_control_migration():
    return render_control_page("Migration", build_migration_body())


@release_control_web_bp.route("/release-control/rollback")
@role_required(*RELEASE_CONTROL_ROLES)
def release_control_rollback():
    return render_control_page("Rollback", build_rollback_body())


@release_control_web_bp.route("/release-control/deployment")
@role_required(*RELEASE_CONTROL_ROLES)
def release_control_deployment():
    return render_control_page("Deployment", build_deployment_body())


@release_control_web_bp.route("/release-control/audit")
@role_required(*RELEASE_CONTROL_ROLES)
def release_control_audit():
    return render_control_page("Audit", build_audit_body())
