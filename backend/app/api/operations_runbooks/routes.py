"""Operations Runbooks API routes — Phase 5 Sprint 5.11."""

from __future__ import annotations

from flask import Blueprint

from app.services.operations_runbooks_service import (
    backup_runbook,
    dashboard_payload,
    go_live_runbook,
    incident_runbook,
    operations_runbooks_inventory,
    operations_runbooks_readiness_report,
    restore_runbook,
    rollback_runbook,
)

operations_runbooks_bp = Blueprint(
    "operations_runbooks_api",
    __name__,
    url_prefix="/api/v1/operations-runbooks",
)


@operations_runbooks_bp.route("/dashboard", methods=["GET"])
def operations_runbooks_dashboard_api():
    return dashboard_payload()


@operations_runbooks_bp.route("/go-live", methods=["GET"])
def operations_runbooks_go_live_api():
    return go_live_runbook()


@operations_runbooks_bp.route("/backup", methods=["GET"])
def operations_runbooks_backup_api():
    return backup_runbook()


@operations_runbooks_bp.route("/restore", methods=["GET"])
def operations_runbooks_restore_api():
    return restore_runbook()


@operations_runbooks_bp.route("/rollback", methods=["GET"])
def operations_runbooks_rollback_api():
    return rollback_runbook()


@operations_runbooks_bp.route("/incident", methods=["GET"])
def operations_runbooks_incident_api():
    return incident_runbook()


@operations_runbooks_bp.route("/inventory", methods=["GET"])
def operations_runbooks_inventory_api():
    return operations_runbooks_inventory()


@operations_runbooks_bp.route("/readiness", methods=["GET"])
def operations_runbooks_readiness_api():
    return operations_runbooks_readiness_report()
