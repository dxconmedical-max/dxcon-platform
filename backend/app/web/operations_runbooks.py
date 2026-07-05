"""Operations Runbooks web routes — Phase 5 Sprint 5.11."""

from __future__ import annotations

from flask import Blueprint

from app.services.operations_runbooks_service import OPERATIONS_RUNBOOKS_ROLES
from app.utils.auth import role_required
from app.web.operations_runbooks_lib import (
    build_backup_body,
    build_dashboard_body,
    build_go_live_body,
    build_incident_body,
    build_restore_body,
    build_rollback_body,
    render_runbooks_page,
)

operations_runbooks_web_bp = Blueprint("operations_runbooks_web", __name__)


@operations_runbooks_web_bp.route("/operations-runbooks")
@role_required(*OPERATIONS_RUNBOOKS_ROLES)
def operations_runbooks_dashboard():
    return render_runbooks_page("Operations Runbooks", build_dashboard_body())


@operations_runbooks_web_bp.route("/operations-runbooks/go-live")
@role_required(*OPERATIONS_RUNBOOKS_ROLES)
def operations_runbooks_go_live():
    return render_runbooks_page("Go-Live Runbook", build_go_live_body())


@operations_runbooks_web_bp.route("/operations-runbooks/backup")
@role_required(*OPERATIONS_RUNBOOKS_ROLES)
def operations_runbooks_backup():
    return render_runbooks_page("Backup Runbook", build_backup_body())


@operations_runbooks_web_bp.route("/operations-runbooks/restore")
@role_required(*OPERATIONS_RUNBOOKS_ROLES)
def operations_runbooks_restore():
    return render_runbooks_page("Restore Runbook", build_restore_body())


@operations_runbooks_web_bp.route("/operations-runbooks/rollback")
@role_required(*OPERATIONS_RUNBOOKS_ROLES)
def operations_runbooks_rollback():
    return render_runbooks_page("Rollback Runbook", build_rollback_body())


@operations_runbooks_web_bp.route("/operations-runbooks/incident")
@role_required(*OPERATIONS_RUNBOOKS_ROLES)
def operations_runbooks_incident():
    return render_runbooks_page("Incident Runbook", build_incident_body())
