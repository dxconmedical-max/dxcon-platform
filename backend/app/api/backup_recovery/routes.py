"""Backup & Disaster Recovery API routes — Phase 5 Sprint 5.3."""

from __future__ import annotations

from flask import Blueprint, request

from app.services.backup_recovery_service import (
    BackupRecoveryError,
    backup_dashboard,
    backup_readiness_report,
    backup_scheduler,
    dashboard_payload,
    disaster_recovery_runbook,
    pitr_checklist,
    restore_verification,
    run_restore_dry_run,
)

backup_recovery_bp = Blueprint(
    "backup_recovery_api",
    __name__,
    url_prefix="/api/v1/backup-recovery",
)


@backup_recovery_bp.route("/dashboard", methods=["GET"])
def backup_recovery_dashboard_api():
    return dashboard_payload()


@backup_recovery_bp.route("/scheduler", methods=["GET"])
def backup_recovery_scheduler_api():
    return backup_scheduler()


@backup_recovery_bp.route("/restore", methods=["GET"])
def backup_recovery_restore_api():
    limit = int(request.args.get("limit") or 25)
    return restore_verification(limit=limit)


@backup_recovery_bp.route("/restore/dry-run", methods=["POST"])
def backup_recovery_restore_dry_run_api():
    data = request.get_json(silent=True) or {}
    try:
        return run_restore_dry_run(data.get("backup_id"))
    except BackupRecoveryError as exc:
        return {"error": exc.message}, exc.status_code


@backup_recovery_bp.route("/pitr", methods=["GET"])
def backup_recovery_pitr_api():
    return pitr_checklist()


@backup_recovery_bp.route("/runbook", methods=["GET"])
def backup_recovery_runbook_api():
    return disaster_recovery_runbook()


@backup_recovery_bp.route("/inventory", methods=["GET"])
def backup_recovery_inventory_api():
    return backup_dashboard()


@backup_recovery_bp.route("/readiness", methods=["GET"])
def backup_recovery_readiness_api():
    return backup_readiness_report()
