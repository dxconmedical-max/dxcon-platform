"""Release Management API routes — Phase 5 Sprint 5.7."""

from __future__ import annotations

from flask import Blueprint

from app.services.release_management_service import (
    dashboard_payload,
    migration_status,
    release_environment,
    release_health,
    release_management_dashboard,
    release_management_readiness_report,
    release_notes,
    release_rollback,
    release_version,
)

release_management_bp = Blueprint(
    "release_management_api",
    __name__,
    url_prefix="/api/v1/release-management",
)


@release_management_bp.route("/dashboard", methods=["GET"])
def release_management_dashboard_api():
    return dashboard_payload()


@release_management_bp.route("/environment", methods=["GET"])
def release_management_environment_api():
    return release_environment()


@release_management_bp.route("/version", methods=["GET"])
def release_management_version_api():
    return release_version()


@release_management_bp.route("/notes", methods=["GET"])
def release_management_notes_api():
    return release_notes()


@release_management_bp.route("/migration", methods=["GET"])
def release_management_migration_api():
    return migration_status()


@release_management_bp.route("/health", methods=["GET"])
def release_management_health_api():
    return release_health()


@release_management_bp.route("/rollback", methods=["GET"])
def release_management_rollback_api():
    return release_rollback()


@release_management_bp.route("/inventory", methods=["GET"])
def release_management_inventory_api():
    return release_management_dashboard()


@release_management_bp.route("/readiness", methods=["GET"])
def release_management_readiness_api():
    return release_management_readiness_report()
