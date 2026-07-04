"""Backup & Disaster Recovery web routes — Phase 5 Sprint 5.3."""

from __future__ import annotations

from flask import Blueprint

from app.services.backup_recovery_service import BACKUP_RECOVERY_ROLES
from app.utils.auth import role_required
from app.web.backup_recovery_lib import (
    build_dashboard_body,
    build_pitr_body,
    build_restore_body,
    build_runbook_body,
    build_scheduler_body,
    render_backup_page,
)

backup_recovery_web_bp = Blueprint("backup_recovery_web", __name__)


@backup_recovery_web_bp.route("/backup-recovery")
@role_required(*BACKUP_RECOVERY_ROLES)
def backup_recovery_dashboard():
    return render_backup_page("Backup Dashboard", build_dashboard_body())


@backup_recovery_web_bp.route("/backup-recovery/scheduler")
@role_required(*BACKUP_RECOVERY_ROLES)
def backup_recovery_scheduler():
    return render_backup_page("Backup Scheduler", build_scheduler_body())


@backup_recovery_web_bp.route("/backup-recovery/restore")
@role_required(*BACKUP_RECOVERY_ROLES)
def backup_recovery_restore():
    return render_backup_page("Restore Verification", build_restore_body())


@backup_recovery_web_bp.route("/backup-recovery/pitr")
@role_required(*BACKUP_RECOVERY_ROLES)
def backup_recovery_pitr():
    return render_backup_page("PITR Checklist", build_pitr_body())


@backup_recovery_web_bp.route("/backup-recovery/runbook")
@role_required(*BACKUP_RECOVERY_ROLES)
def backup_recovery_runbook():
    return render_backup_page("Disaster Recovery Runbook", build_runbook_body())
