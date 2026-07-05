"""Release Control API routes — Phase 5 Sprint 5.12."""

from __future__ import annotations

from flask import Blueprint, request

from app.services.release_control_service import (
    dashboard_payload,
    deployment_metrics,
    migration_metrics,
    release_audit,
    release_control_readiness_report,
    release_history,
    rollback_metrics,
    version_compare,
)

release_control_bp = Blueprint(
    "release_control_api",
    __name__,
    url_prefix="/api/v1/release-control",
)


@release_control_bp.route("/dashboard", methods=["GET"])
def release_control_dashboard_api():
    return dashboard_payload()


@release_control_bp.route("/history", methods=["GET"])
def release_control_history_api():
    limit = min(max(int(request.args.get("limit", 25)), 1), 100)
    return release_history(limit=limit)


@release_control_bp.route("/version-compare", methods=["GET"])
def release_control_version_compare_api():
    return version_compare(request.args.get("baseline"))


@release_control_bp.route("/migration", methods=["GET"])
def release_control_migration_api():
    return migration_metrics()


@release_control_bp.route("/rollback", methods=["GET"])
def release_control_rollback_api():
    return rollback_metrics()


@release_control_bp.route("/deployment", methods=["GET"])
def release_control_deployment_api():
    return deployment_metrics()


@release_control_bp.route("/audit", methods=["GET"])
def release_control_audit_api():
    limit = min(max(int(request.args.get("limit", 50)), 1), 200)
    return release_audit(limit=limit)


@release_control_bp.route("/readiness", methods=["GET"])
def release_control_readiness_api():
    return release_control_readiness_report()
