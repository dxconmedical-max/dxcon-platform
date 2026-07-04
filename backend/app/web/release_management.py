"""Release Management web routes — Phase 5 Sprint 5.7."""

from __future__ import annotations

from flask import Blueprint

from app.services.release_management_service import RELEASE_MANAGEMENT_ROLES
from app.utils.auth import role_required
from app.web.release_management_lib import (
    build_dashboard_body,
    build_environment_body,
    build_health_body,
    build_migration_body,
    build_notes_body,
    build_rollback_body,
    build_version_body,
    render_release_page,
)

release_management_web_bp = Blueprint("release_management_web", __name__)


@release_management_web_bp.route("/release-management")
@role_required(*RELEASE_MANAGEMENT_ROLES)
def release_management_dashboard():
    return render_release_page("Release Management", build_dashboard_body())


@release_management_web_bp.route("/release-management/environment")
@role_required(*RELEASE_MANAGEMENT_ROLES)
def release_management_environment():
    return render_release_page("Environment", build_environment_body())


@release_management_web_bp.route("/release-management/version")
@role_required(*RELEASE_MANAGEMENT_ROLES)
def release_management_version():
    return render_release_page("Version", build_version_body())


@release_management_web_bp.route("/release-management/notes")
@role_required(*RELEASE_MANAGEMENT_ROLES)
def release_management_notes():
    return render_release_page("Release Notes", build_notes_body())


@release_management_web_bp.route("/release-management/migration")
@role_required(*RELEASE_MANAGEMENT_ROLES)
def release_management_migration():
    return render_release_page("Migration Status", build_migration_body())


@release_management_web_bp.route("/release-management/health")
@role_required(*RELEASE_MANAGEMENT_ROLES)
def release_management_health():
    return render_release_page("Health", build_health_body())


@release_management_web_bp.route("/release-management/rollback")
@role_required(*RELEASE_MANAGEMENT_ROLES)
def release_management_rollback():
    return render_release_page("Rollback", build_rollback_body())
