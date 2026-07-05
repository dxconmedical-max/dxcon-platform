"""Release control business logic for Phase 5 Sprint 5.12."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from app.core.build_info import build_info
from app.models.audit_log import AuditLog
from app.models.operations_platform import DeploymentRecord
from app.operations.deployment_service import DeploymentService
from app.services.production_deployment_service import rolling_deployment
from app.services.release_management_service import (
    migration_status,
    release_rollback,
    release_version,
)
from app.services.reporting_service import _safe

RELEASE_CONTROL_ROLES = ("SUPER_ADMIN", "ADMIN")

ROOT = Path(__file__).resolve().parents[2]
REPO = ROOT.parent
GENERATED = ROOT / "generated_release"

HISTORY_REPORTS = (
    "RC1_REPORT.json",
    "RC2_REPORT.json",
    "GA_REPORT.json",
    "RELEASE_MANAGEMENT_REPORT.json",
    "PRODUCTION_DEPLOYMENT_REPORT.json",
    "EXECUTIVE_METRICS_REPORT.json",
    "AI_OPERATIONS_REPORT.json",
    "OPERATIONS_RUNBOOKS_REPORT.json",
    "PILOT_STATUS_REPORT.json",
    "BACKUP_RECOVERY_REPORT.json",
    "MONITORING_CENTER_REPORT.json",
    "SECURITY_READINESS_REPORT.json",
)

RELEASE_AUDIT_ACTIONS = (
    "DEPLOY",
    "DEPLOYMENT",
    "ROLLBACK",
    "MIGRATION",
    "RELEASE",
    "BUILD",
)

FEATURES = (
    "Release History",
    "Version Compare",
    "Migration",
    "Rollback",
    "Deployment",
    "Audit",
)


def ensure_release_control() -> dict[str, Any]:
    return {"ready": True, "read_only": True}


def _load_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def release_history(limit: int = 25) -> dict[str, Any]:
    ensure_release_control()
    deployments = _safe(
        lambda: DeploymentRecord.query.order_by(DeploymentRecord.created_at.desc()).limit(limit).all(),
        [],
    )
    entries: list[dict[str, Any]] = []
    for record in deployments:
        entries.append(
            {
                "type": "deployment",
                "version": record.version,
                "label": record.deployment_code,
                "status": record.status,
                "environment": record.environment,
                "generated_at": record.created_at.isoformat() if record.created_at else None,
                "readiness_score": record.readiness_score,
                "build_sha": record.build_sha,
            }
        )

    for filename in HISTORY_REPORTS:
        payload = _load_json(GENERATED / filename)
        if not payload:
            continue
        summary = payload.get("summary", {})
        entries.append(
            {
                "type": "verify_report",
                "version": payload.get("release") or f"Phase {payload.get('phase', '?')}",
                "label": payload.get("sprint", filename.replace("_REPORT.json", "")),
                "status": "OK" if summary.get("ok", True) else "WARN",
                "environment": "platform",
                "generated_at": payload.get("generated_at"),
                "readiness_score": summary.get("score"),
                "build_sha": None,
                "source_file": filename,
            }
        )

    entries.sort(key=lambda row: row.get("generated_at") or "", reverse=True)
    for index, row in enumerate(entries, start=1):
        row["sequence"] = index

    return {
        "report": "release_history",
        "read_only": True,
        "entries_total": len(entries),
        "deployments_total": len(deployments),
        "reports_total": len(entries) - len(deployments),
        "entries": entries[:limit],
    }


def version_compare(baseline: str | None = None) -> dict[str, Any]:
    ensure_release_control()
    current = release_version()
    info = build_info()
    migration = migration_status()

    baseline_record = None
    if baseline:
        baseline_record = _safe(
            lambda: DeploymentRecord.query.filter(
                (DeploymentRecord.version == baseline) | (DeploymentRecord.deployment_code == baseline)
            )
            .order_by(DeploymentRecord.created_at.desc())
            .first()
        )
    if baseline_record is None:
        baseline_record = _safe(
            lambda: DeploymentRecord.query.order_by(DeploymentRecord.created_at.desc()).offset(1).first()
        )

    rc1 = _load_json(GENERATED / "RC1_REPORT.json") or {}
    baseline_version = (
        baseline_record.version
        if baseline_record
        else rc1.get("release", "v1.0.0-rc1")
    )
    baseline_sha = baseline_record.build_sha if baseline_record else None

    current_fields = {
        "version": current.get("version"),
        "git_sha": current.get("git_sha"),
        "build_time": current.get("build_time"),
        "environment": current.get("environment"),
        "migration_status": migration.get("status"),
    }
    baseline_fields = {
        "version": baseline_version,
        "git_sha": baseline_sha,
        "build_time": baseline_record.build_time.isoformat() if baseline_record and baseline_record.build_time else None,
        "environment": baseline_record.environment if baseline_record else info.get("environment"),
        "migration_status": migration.get("status"),
    }

    differences = []
    for field in current_fields:
        current_value = current_fields[field]
        baseline_value = baseline_fields[field]
        if current_value != baseline_value:
            differences.append(
                {
                    "field": field,
                    "current": current_value,
                    "baseline": baseline_value,
                    "changed": True,
                }
            )
        else:
            differences.append(
                {
                    "field": field,
                    "current": current_value,
                    "baseline": baseline_value,
                    "changed": False,
                }
            )

    return {
        "report": "version_compare",
        "read_only": True,
        "current": current_fields,
        "baseline": baseline_fields,
        "baseline_source": baseline_record.deployment_code if baseline_record else "RC1_REPORT.json",
        "differences": differences,
        "fields_changed": sum(1 for row in differences if row["changed"]),
        "rc1_score": rc1.get("score", {}).get("score"),
    }


def migration_metrics() -> dict[str, Any]:
    ensure_release_control()
    payload = migration_status()
    payload["report"] = "migration_metrics"
    return payload


def rollback_metrics() -> dict[str, Any]:
    ensure_release_control()
    payload = release_rollback()
    payload["report"] = "rollback_metrics"
    plan = _safe(DeploymentService.rollback_plan, None)
    if plan:
        payload["live_rollback_plan"] = plan
    return payload


def deployment_metrics() -> dict[str, Any]:
    ensure_release_control()
    current = _safe(DeploymentService.current, {})
    rolling = rolling_deployment()
    version = release_version()
    return {
        "report": "deployment_metrics",
        "read_only": True,
        "current_version": current.get("current_version"),
        "build_sha": current.get("build_sha"),
        "environment": current.get("environment"),
        "last_deployment": current.get("last_deployment"),
        "deployment_checks": current.get("checks", []),
        "rollback_plan_available": current.get("rollback_plan") is not None,
        "rolling_strategy": rolling.get("strategy"),
        "rolling_checks_passed": rolling.get("checks_passed"),
        "rolling_checks_total": rolling.get("checks_total"),
        "deploy_pipeline": rolling.get("pipeline_script"),
        "version_info": {
            "version": version.get("version"),
            "git_sha": version.get("git_sha"),
            "build_time": version.get("build_time"),
        },
        "legacy_api": "GET /api/v1/operations/deployment/current",
    }


def release_audit(limit: int = 50) -> dict[str, Any]:
    ensure_release_control()
    rows = _safe(
        lambda: AuditLog.query.order_by(AuditLog.created_at.desc()).limit(limit * 3).all(),
        [],
    )
    release_rows = []
    for row in rows:
        action = (row.action or "").upper()
        object_type = (row.object_type or "").upper()
        if any(token in action or token in object_type for token in RELEASE_AUDIT_ACTIONS):
            release_rows.append(row.to_dict())
        if len(release_rows) >= limit:
            break

    deployment_records = _safe(
        lambda: DeploymentRecord.query.order_by(DeploymentRecord.created_at.desc()).limit(10).all(),
        [],
    )
    synthetic = []
    for record in deployment_records:
        synthetic.append(
            {
                "id": record.id,
                "user_email": "SYSTEM",
                "action": "DEPLOYMENT_RECORD",
                "object_type": "DeploymentRecord",
                "object_id": record.deployment_code,
                "ip_address": None,
                "request_id": None,
                "created_at": record.created_at.isoformat() if record.created_at else None,
                "detail": {
                    "version": record.version,
                    "status": record.status,
                    "readiness_score": record.readiness_score,
                },
            }
        )

    combined = release_rows + synthetic
    combined.sort(key=lambda row: row.get("created_at") or "", reverse=True)

    return {
        "report": "release_audit",
        "read_only": True,
        "audit_entries": combined[:limit],
        "audit_entries_total": len(combined),
        "platform_audit_matched": len(release_rows),
        "deployment_records_included": len(synthetic),
        "legacy_hub": "/security-compliance/audit",
    }


def release_control_dashboard() -> dict[str, Any]:
    ensure_release_control()
    history = release_history(limit=5)
    compare = version_compare()
    migration = migration_metrics()
    deployment = deployment_metrics()
    audit = release_audit(limit=5)
    status = "OK"
    if migration.get("status") != "READY":
        status = "WARN"
    return {
        "report": "release_control_dashboard",
        "read_only": True,
        "status": status,
        "history_entries": history["entries_total"],
        "fields_changed": compare["fields_changed"],
        "migration_status": migration.get("status"),
        "last_deployment_status": (deployment.get("last_deployment") or {}).get("status"),
        "audit_entries": audit["audit_entries_total"],
    }


def release_control_readiness_report() -> dict[str, Any]:
    dashboard = dashboard_payload()
    return {
        "generated_at": datetime.utcnow().isoformat(),
        "phase": "5.12",
        "sprint": "Release Control",
        "platform": dashboard["platform"],
        "status": dashboard["status"],
        "summary": dashboard["summary"],
        "features": list(FEATURES),
        "sections": {
            "history": release_history(),
            "version_compare": version_compare(),
            "migration": migration_metrics(),
            "rollback": rollback_metrics(),
            "deployment": deployment_metrics(),
            "audit": release_audit(),
        },
        "legacy_routes": [
            "/release-management",
            "/production-deployment",
            "/api/v1/release-management/dashboard",
            "/api/v1/operations/deployment/rollback-plan",
        ],
    }


def dashboard_payload() -> dict[str, Any]:
    ensure_release_control()
    dash = release_control_dashboard()
    history = release_history(limit=10)
    compare = version_compare()
    migration = migration_metrics()
    deployment = deployment_metrics()
    return {
        "platform": "Release Control",
        "phase": "5.12",
        "sprint": "Release Control",
        "status": dash["status"],
        "read_only": True,
        "generated_at": datetime.utcnow().isoformat(),
        "summary": {
            "history_entries": history["entries_total"],
            "deployments_total": history["deployments_total"],
            "fields_changed": compare["fields_changed"],
            "migration_status": migration.get("status"),
            "migration_checks_passed": migration.get("checks_passed", 0),
            "last_deployment_status": (deployment.get("last_deployment") or {}).get("status"),
            "audit_entries": dash["audit_entries"],
        },
        "features": list(FEATURES),
    }
