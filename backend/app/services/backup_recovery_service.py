"""Backup & Disaster Recovery business logic for Phase 5 Sprint 5.3."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from flask import current_app

from app.models.operations_platform import (
    BackupArtifact,
    BackupJob,
    RestoreJob,
    RestoreValidation,
    ScheduledJob,
)
from app.operations.backup_registry import BACKUP_TYPES
from app.operations.backup_service import BackupService, OperationsPlatformError
from app.operations.job_registry import DEFAULT_JOBS
from app.operations.restore_service import RestoreService
from app.services.reporting_service import _safe

BACKUP_RECOVERY_ROLES = ("SUPER_ADMIN", "ADMIN")

ROOT = Path(__file__).resolve().parents[2]
REPO = ROOT.parent

DEPLOYMENT_SCRIPTS = {
    "backup_postgres": REPO / "deployment" / "scripts" / "backup_postgres.sh",
    "restore_dry_run": REPO / "deployment" / "scripts" / "restore_postgres_dry_run.sh",
    "backup_uploads": REPO / "deployment" / "scripts" / "backup_uploads.sh",
}

DOCS = {
    "backup": REPO / "docs" / "BACKUP.md",
    "disaster_recovery": REPO / "docs" / "DISASTER_RECOVERY.md",
    "restore": REPO / "docs" / "RESTORE.md",
}

FEATURES = (
    "Backup Scheduler",
    "Restore Verification",
    "PITR Checklist",
    "Disaster Recovery Runbook",
    "Backup Dashboard",
)


class BackupRecoveryError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


def ensure_backup_recovery() -> dict[str, Any]:
    return {"ready": True, "read_only": True}


def backup_scheduler() -> dict[str, Any]:
    ensure_backup_recovery()
    jobs = _safe(
        lambda: ScheduledJob.query.filter(ScheduledJob.handler.like("backup.%"))
        .order_by(ScheduledJob.job_code.asc())
        .all(),
        [],
    )
    default = [item for item in DEFAULT_JOBS if item["handler"].startswith("backup.")]
    return {
        "report": "backup_scheduler",
        "read_only": True,
        "scheduled_jobs": [row.to_dict() for row in jobs],
        "default_jobs": default,
        "handlers": ["backup.database"],
        "backup_types": list(BACKUP_TYPES),
        "recommended_cron": "0 2 * * *",
        "api_trigger": "POST /api/v1/operations/backups/run",
    }


def restore_verification(limit: int = 25) -> dict[str, Any]:
    ensure_backup_recovery()
    restores = RestoreService.list_restores()
    validations = _safe(
        lambda: RestoreValidation.query.order_by(RestoreValidation.created_at.desc())
        .limit(limit)
        .all(),
        [],
    )
    passed = sum(1 for row in validations if row.status == "PASSED")
    return {
        "report": "restore_verification",
        "read_only": True,
        "restore_jobs_total": restores.get("count", 0),
        "validations_total": len(validations),
        "validations_passed": passed,
        "recent_restores": restores.get("restores", [])[:10],
        "recent_validations": [row.to_dict() for row in validations],
        "dry_run_api": "POST /api/v1/operations/restores/dry-run",
    }


def run_restore_dry_run(backup_id: str | None = None) -> dict[str, Any]:
    ensure_backup_recovery()
    try:
        payload = RestoreService.dry_run({"backup_id": backup_id} if backup_id else {})
    except OperationsPlatformError as exc:
        raise BackupRecoveryError(exc.message, exc.status_code) from exc
    payload["read_only"] = False
    payload["destructive"] = False
    return payload


def pitr_checklist() -> dict[str, Any]:
    ensure_backup_recovery()
    app = current_app._get_current_object()
    db_engine = app.config.get("SQLALCHEMY_DATABASE_URI", "").split(":", 1)[0]
    items = [
        {
            "id": 1,
            "title": "Define RPO and RTO targets",
            "detail": "Production API RTO 4h / RPO 1h per disaster recovery policy.",
            "status": "DOCUMENTED",
        },
        {
            "id": 2,
            "title": "Enable automated base backups",
            "detail": "Nightly database backup via OPS-BACKUP-NIGHTLY or cloud provider snapshots.",
            "status": "PASS" if BackupJob.query.count() > 0 else "WARN",
        },
        {
            "id": 3,
            "title": "Configure WAL / point-in-time recovery",
            "detail": "Enable WAL archiving on PostgreSQL for PITR (production managed DB).",
            "status": "PASS" if app.config.get("DATABASE_PITR_ENABLED") else "MANUAL",
        },
        {
            "id": 4,
            "title": "Validate backup artifacts",
            "detail": "Run restore dry-run and checksum validation before pilot go-live.",
            "status": "PASS"
            if RestoreValidation.query.filter_by(status="PASSED").count() > 0
            else "WARN",
        },
        {
            "id": 5,
            "title": "Document retention policy",
            "detail": "Retain daily backups for at least 30 days.",
            "status": "PASS",
        },
        {
            "id": 6,
            "title": "Quarterly DR drill",
            "detail": "Execute deployment/scripts/restore_postgres_dry_run.sh and verify report.",
            "status": "SCHEDULED",
        },
    ]
    return {
        "report": "pitr_checklist",
        "read_only": True,
        "database_engine": db_engine,
        "pitr_enabled_config": bool(app.config.get("DATABASE_PITR_ENABLED")),
        "items": items,
        "items_passed": sum(1 for item in items if item["status"] in ("PASS", "DOCUMENTED")),
        "items_total": len(items),
    }


def disaster_recovery_runbook() -> dict[str, Any]:
    ensure_backup_recovery()
    scenarios = [
        {
            "id": "database_loss",
            "title": "Database loss",
            "steps": [
                "Fail over to standby or restore from latest backup.",
                "Follow docs/RESTORE.md.",
                "Validate core tables: users, patients, orders.",
            ],
            "links": ["/backup-recovery/restore", "/api/v1/operations/backups"],
        },
        {
            "id": "region_loss",
            "title": "Region / cluster loss",
            "steps": [
                "Provision standby stack from deployment/ manifests.",
                "Restore PostgreSQL and object storage.",
                "Update DNS/ingress and run Enterprise sign-off verification.",
            ],
            "links": ["/backup-recovery/pitr", "/monitoring"],
        },
        {
            "id": "app_regression",
            "title": "Application regression",
            "steps": [
                "GET /api/v1/operations/deployment/rollback-plan",
                "Redeploy prior container tag (BUILD_VERSION).",
                "Confirm smoke and security preflight pass.",
            ],
            "links": ["/operations/deployment", "/security-compliance"],
        },
    ]
    docs_available = {name: path.exists() for name, path in DOCS.items()}
    scripts_available = {name: path.exists() for name, path in DEPLOYMENT_SCRIPTS.items()}
    return {
        "report": "disaster_recovery_runbook",
        "read_only": True,
        "objectives": {
            "production_api": {"rto_hours": 4, "rpo_hours": 1},
            "file_storage": {"rto_hours": 8, "rpo_hours": 4},
        },
        "scenarios": scenarios,
        "communication": [
            "Page on-call via Alertmanager.",
            "Record incident in operations audit trail.",
        ],
        "docs_available": docs_available,
        "deployment_scripts": scripts_available,
        "verification_script": "backend/scripts/verify_backup_recovery.py",
    }


def backup_dashboard() -> dict[str, Any]:
    ensure_backup_recovery()
    backups = BackupService.list_backups()
    scheduler = backup_scheduler()
    restore = restore_verification(limit=5)
    pitr = pitr_checklist()
    artifacts = _safe(lambda: BackupArtifact.query.count(), 0)
    latest = backups.get("backups", [])[:5]
    status = "OK"
    if backups.get("count", 0) == 0:
        status = "WARN"
    if restore["validations_passed"] == 0 and restore["validations_total"] == 0:
        status = "WARN" if status == "OK" else status
    return {
        "report": "backup_dashboard",
        "read_only": True,
        "status": status,
        "backups_total": backups.get("count", 0),
        "artifacts_total": artifacts,
        "backup_types": backups.get("backup_types", []),
        "latest_backups": latest,
        "scheduled_backup_jobs": len(scheduler.get("scheduled_jobs", [])),
        "restore_validations_passed": restore["validations_passed"],
        "pitr_items_passed": pitr["items_passed"],
    }


def backup_readiness_report() -> dict[str, Any]:
    dashboard = dashboard_payload()
    return {
        "generated_at": datetime.utcnow().isoformat(),
        "phase": "5.3",
        "sprint": "Backup & Disaster Recovery",
        "platform": dashboard["platform"],
        "status": dashboard["status"],
        "summary": dashboard["summary"],
        "features": list(FEATURES),
        "sections": {
            "scheduler": backup_scheduler(),
            "restore": restore_verification(limit=10),
            "pitr": pitr_checklist(),
            "runbook": disaster_recovery_runbook(),
            "dashboard": backup_dashboard(),
        },
    }


def dashboard_payload() -> dict[str, Any]:
    ensure_backup_recovery()
    dash = backup_dashboard()
    scheduler = backup_scheduler()
    restore = restore_verification(limit=5)
    pitr = pitr_checklist()
    return {
        "platform": "Backup & Disaster Recovery",
        "phase": "5.3",
        "sprint": "Backup & Disaster Recovery",
        "status": dash["status"],
        "read_only": True,
        "generated_at": datetime.utcnow().isoformat(),
        "summary": {
            "backups_total": dash["backups_total"],
            "artifacts_total": dash["artifacts_total"],
            "scheduled_jobs": len(scheduler.get("scheduled_jobs", [])),
            "restore_validations_passed": restore["validations_passed"],
            "pitr_checklist_passed": pitr["items_passed"],
            "pitr_checklist_total": pitr["items_total"],
            "deployment_scripts_available": sum(
                1 for path in DEPLOYMENT_SCRIPTS.values() if path.exists()
            ),
        },
        "features": list(FEATURES),
    }
