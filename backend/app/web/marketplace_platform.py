"""Marketplace Platform web routes — Phase 7.2."""

from __future__ import annotations

from flask import Blueprint

from app.services.marketplace_platform_service import MARKETPLACE_PLATFORM_ROLES
from app.utils.auth import role_required
from app.web.marketplace_platform_lib import (
    build_dashboard_body,
    build_dependencies_body,
    build_health_body,
    build_installer_body,
    build_manifest_body,
    build_marketplace_body,
    build_permissions_body,
    build_registry_body,
    build_sandbox_body,
    build_versions_body,
    render_mp_page,
)

marketplace_platform_web_bp = Blueprint("marketplace_platform_web", __name__)


@marketplace_platform_web_bp.route("/marketplace-platform")
@role_required(*MARKETPLACE_PLATFORM_ROLES)
def marketplace_platform_dashboard():
    return render_mp_page("Marketplace Platform", build_dashboard_body())


@marketplace_platform_web_bp.route("/marketplace-platform/marketplace")
@role_required(*MARKETPLACE_PLATFORM_ROLES)
def marketplace_platform_marketplace():
    return render_mp_page("Marketplace", build_marketplace_body())


@marketplace_platform_web_bp.route("/marketplace-platform/registry")
@role_required(*MARKETPLACE_PLATFORM_ROLES)
def marketplace_platform_registry():
    return render_mp_page("Plugin Registry", build_registry_body())


@marketplace_platform_web_bp.route("/marketplace-platform/manifest")
@role_required(*MARKETPLACE_PLATFORM_ROLES)
def marketplace_platform_manifest():
    return render_mp_page("Plugin Manifest", build_manifest_body())


@marketplace_platform_web_bp.route("/marketplace-platform/installer")
@role_required(*MARKETPLACE_PLATFORM_ROLES)
def marketplace_platform_installer():
    return render_mp_page("Plugin Installer", build_installer_body())


@marketplace_platform_web_bp.route("/marketplace-platform/versions")
@role_required(*MARKETPLACE_PLATFORM_ROLES)
def marketplace_platform_versions():
    return render_mp_page("Plugin Version", build_versions_body())


@marketplace_platform_web_bp.route("/marketplace-platform/dependencies")
@role_required(*MARKETPLACE_PLATFORM_ROLES)
def marketplace_platform_dependencies():
    return render_mp_page("Plugin Dependency", build_dependencies_body())


@marketplace_platform_web_bp.route("/marketplace-platform/permissions")
@role_required(*MARKETPLACE_PLATFORM_ROLES)
def marketplace_platform_permissions():
    return render_mp_page("Plugin Permission", build_permissions_body())


@marketplace_platform_web_bp.route("/marketplace-platform/sandbox")
@role_required(*MARKETPLACE_PLATFORM_ROLES)
def marketplace_platform_sandbox():
    return render_mp_page("Plugin Sandbox", build_sandbox_body())


@marketplace_platform_web_bp.route("/marketplace-platform/health")
@role_required(*MARKETPLACE_PLATFORM_ROLES)
def marketplace_platform_health():
    return render_mp_page("Plugin Health", build_health_body())
