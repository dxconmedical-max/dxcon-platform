"""Marketplace Platform API routes — Phase 7.2."""

from __future__ import annotations

from flask import Blueprint, request

from app.services.marketplace_platform_service import (
    dashboard_payload,
    marketplace_overview,
    marketplace_platform_readiness_report,
    plugin_dependencies,
    plugin_health,
    plugin_installer,
    plugin_manifest_detail,
    plugin_manifests,
    plugin_permissions,
    plugin_registry,
    plugin_sandbox,
    plugin_versions,
)

marketplace_platform_bp = Blueprint(
    "marketplace_platform_api",
    __name__,
    url_prefix="/api/v1/marketplace-platform",
)


@marketplace_platform_bp.route("/dashboard", methods=["GET"])
def marketplace_platform_dashboard_api():
    return dashboard_payload()


@marketplace_platform_bp.route("/marketplace", methods=["GET"])
def marketplace_platform_marketplace_api():
    return marketplace_overview()


@marketplace_platform_bp.route("/registry", methods=["GET"])
def marketplace_platform_registry_api():
    return plugin_registry()


@marketplace_platform_bp.route("/manifest", methods=["GET"])
def marketplace_platform_manifests_api():
    return plugin_manifests()


@marketplace_platform_bp.route("/manifest/<plugin_id>", methods=["GET"])
def marketplace_platform_manifest_detail_api(plugin_id):
    return plugin_manifest_detail(plugin_id)


@marketplace_platform_bp.route("/installer", methods=["GET"])
def marketplace_platform_installer_api():
    return plugin_installer()


@marketplace_platform_bp.route("/versions", methods=["GET"])
def marketplace_platform_versions_api():
    return plugin_versions()


@marketplace_platform_bp.route("/dependencies", methods=["GET"])
def marketplace_platform_dependencies_api():
    return plugin_dependencies()


@marketplace_platform_bp.route("/permissions", methods=["GET"])
def marketplace_platform_permissions_api():
    return plugin_permissions()


@marketplace_platform_bp.route("/sandbox", methods=["GET"])
def marketplace_platform_sandbox_api():
    plugin_id = request.args.get("plugin_id")
    return plugin_sandbox(plugin_id)


@marketplace_platform_bp.route("/health", methods=["GET"])
def marketplace_platform_health_api():
    return plugin_health()


@marketplace_platform_bp.route("/readiness", methods=["GET"])
def marketplace_platform_readiness_api():
    return marketplace_platform_readiness_report()
