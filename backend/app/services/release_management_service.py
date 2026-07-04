"""Release management business logic for Phase 5 Sprint 5.7."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from flask import current_app

from app.core.build_info import build_info
from app.core.database_startup import verify_migrations
from app.core.deployment import deployment_readiness
from app.infrastructure.infrastructure_services import InfrastructureHealthService
from app.infrastructure.production_health import health_payload, live_payload, ready_payload
from app.operations.deployment_service import DeploymentService
from app.runtime.runtime_config import RuntimeConfig
from app.services.reporting_service import _safe

RELEASE_MANAGEMENT_ROLES = ("SUPER_ADMIN", "ADMIN")

ROOT = Path(__file__).resolve().parents[2]
REPO = ROOT.parent
GENERATED = ROOT / "generated_release"

RELEASE_ASSETS = {
    "rc1_report": GENERATED / "RC1_REPORT.json",
    "rc1_checklist": GENERATED / "RC1_CHECKLIST.json",
    "deployment_guide": REPO / "docs" / "DEPLOYMENT.md",
    "operations_guide": REPO / "docs" / "OPERATIONS.md",
    "rollback_pipeline": REPO / "deployment" / "pipeline" / "rollback.py",
    "deploy_pipeline": REPO / "deployment" / "pipeline" / "deploy.py",
}

PHASE_REPORTS = (
    "PILOT_STATUS_REPORT.json",
    "PRODUCTION_DEPLOYMENT_REPORT.json",
    "TENANT_ISOLATION_REPORT.json",
    "BACKUP_RECOVERY_REPORT.json",
    "MONITORING_CENTER_REPORT.json",
    "SECURITY_READINESS_REPORT.json",
)

FEATURES = (
    "Environment",
    "Version",
    "Release Notes",
    "Migration Status",
    "Health",
    "Rollback",
)


class ReleaseManagementError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


def ensure_release_management() -> dict[str, Any]:
    return {"ready": True, "read_only": True}


def _load_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def release_environment() -> dict[str, Any]:
    ensure_release_management()
    app = current_app._get_current_object()
    runtime = RuntimeConfig.load(app)
    info = build_info()
    deployment = deployment_readiness(app)
    return {
        "report": "environment",
        "read_only": True,
        "app_env": info.get("environment"),
        "runtime_profile": runtime.get("profile"),
        "provider": runtime.get("environment", {}).get("provider"),
        "database_uri_prefix": runtime.get("database_uri_prefix"),
        "feature_flags_count": len(runtime.get("feature_flags", {})),
        "deployment_score": deployment.get("score"),
        "ready_for_production": deployment.get("ready_for_production"),
        "settings": runtime.get("settings", {}),
        "legacy_api": "GET /api/v1/infrastructure/config",
    }


def release_version() -> dict[str, Any]:
    ensure_release_management()
    info = build_info()
    app = current_app._get_current_object()
    deployment = _safe(DeploymentService.current, {})
    return {
        "report": "version",
        "read_only": True,
        "version": info.get("version"),
        "git_sha": info.get("git_sha"),
        "build_time": info.get("build_time"),
        "service": info.get("service"),
        "environment": info.get("environment"),
        "last_deployment": deployment.get("last_deployment"),
        "build_env_vars": ["BUILD_VERSION", "GIT_SHA", "BUILD_TIME", "APP_ENV"],
    }


def release_notes() -> dict[str, Any]:
    ensure_release_management()
    info = build_info()
    rc1 = _load_json(RELEASE_ASSETS["rc1_report"]) or {}
    notes = []
    if rc1:
        notes.append(
            {
                "version": rc1.get("release", "v1.0.0-rc1"),
                "title": "Release Candidate 1",
                "summary": f"RC1 readiness score {rc1.get('score', {}).get('score', 0)}%",
                "generated_at": rc1.get("generated_at"),
            }
        )
    for filename in PHASE_REPORTS:
        payload = _load_json(GENERATED / filename)
        if not payload:
            continue
        notes.append(
            {
                "version": f"Phase {payload.get('phase', '?')}",
                "title": payload.get("sprint", filename.replace("_REPORT.json", "").replace("_", " ").title()),
                "summary": (
                    f"Verify score {payload.get('summary', {}).get('score', 0)}% · "
                    f"{payload.get('summary', {}).get('checks_passed', 0)}/"
                    f"{payload.get('summary', {}).get('checks_total', 0)} checks"
                ),
                "generated_at": payload.get("generated_at"),
            }
        )
    notes.append(
        {
            "version": info.get("version"),
            "title": "Current Build",
            "summary": "Active platform build tracked via BUILD_VERSION and GIT_SHA.",
            "generated_at": datetime.utcnow().isoformat(),
        }
    )
    return {
        "report": "release_notes",
        "read_only": True,
        "current_version": info.get("version"),
        "notes": notes,
        "sources": {
            name: path.exists() for name, path in RELEASE_ASSETS.items() if name.endswith("_report") or name.endswith("_checklist")
        },
        "deployment_guide": str(RELEASE_ASSETS["deployment_guide"].relative_to(REPO))
        if RELEASE_ASSETS["deployment_guide"].exists()
        else None,
    }


def migration_status() -> dict[str, Any]:
    ensure_release_management()
    app = current_app._get_current_object()
    migration = _safe(lambda: verify_migrations(app), {"ready": False})
    stored = app.extensions.get("dxcon_deployment", {}).get("migration_status", {})
    if stored:
        migration = {**stored, **migration}
    checks = [
        {
            "id": 1,
            "title": "Core tables present",
            "detail": "users, patients, orders available in schema.",
            "status": "PASS" if migration.get("ready") else "FAIL",
        },
        {
            "id": 2,
            "title": "Alembic tracking",
            "detail": "alembic_version table present when migrations configured.",
            "status": "PASS" if migration.get("alembic_present") else "MANUAL",
        },
        {
            "id": 3,
            "title": "Startup validation",
            "detail": "STARTUP_VALIDATE_DB runs migration checks on boot.",
            "status": "PASS" if app.config.get("STARTUP_VALIDATE_DB", True) else "WARN",
        },
    ]
    return {
        "report": "migration_status",
        "read_only": True,
        "status": "READY" if migration.get("ready") else "PENDING",
        "migration": migration,
        "table_count": migration.get("table_count", 0),
        "missing_core_tables": migration.get("missing_core_tables", []),
        "checks": checks,
        "checks_passed": sum(1 for item in checks if item["status"] == "PASS"),
        "checks_total": len(checks),
        "legacy_api": "GET /api/v1/system/ready",
    }


def release_health() -> dict[str, Any]:
    ensure_release_management()
    app = current_app._get_current_object()
    live, live_code = live_payload(app)
    ready, ready_code = ready_payload(app)
    health, health_code = health_payload(app)
    infra = _safe(lambda: InfrastructureHealthService.status(app), {})
    return {
        "report": "health",
        "read_only": True,
        "live": {"path": "/live", "status_code": live_code, "payload": live},
        "ready": {"path": "/ready", "status_code": ready_code, "payload": ready},
        "health": {"path": "/api/v1/system/health", "status_code": health_code, "payload": health},
        "infrastructure_status": infra.get("status"),
        "deployment_score": infra.get("deployment_score"),
        "probe_paths": ["/live", "/ready", "/api/v1/system/health", "/api/v1/system/liveness"],
    }


def release_rollback() -> dict[str, Any]:
    ensure_release_management()
    plan = _safe(DeploymentService.rollback_plan, None)
    pipeline_steps = [
        "Validate backup artifacts",
        "Run restore dry-run",
        "Deploy previous container image tag (BUILD_VERSION)",
        "Run post-deployment verification",
    ]
    items = [
        {"id": 1, "item": "Capture current BUILD_VERSION and GIT_SHA", "required": True},
        {"id": 2, "item": "GET /api/v1/operations/deployment/rollback-plan", "required": True},
        {"id": 3, "item": "Run deployment/pipeline/rollback.py", "required": True},
        {"id": 4, "item": "Verify /live and /ready after rollback", "required": True},
        {"id": 5, "item": "Confirm migration compatibility for target version", "required": True},
    ]
    return {
        "report": "rollback",
        "read_only": True,
        "rollback_plan": plan,
        "pipeline_steps": pipeline_steps,
        "items": items,
        "pipeline_script": str(RELEASE_ASSETS["rollback_pipeline"].relative_to(REPO)),
        "pipeline_available": RELEASE_ASSETS["rollback_pipeline"].exists(),
        "legacy_api": "GET /api/v1/operations/deployment/rollback-plan",
        "related_hub": "/production-deployment/rollback",
    }


def release_management_dashboard() -> dict[str, Any]:
    ensure_release_management()
    env = release_environment()
    version = release_version()
    migration = migration_status()
    health = release_health()
    status = "OK"
    if migration["status"] != "READY":
        status = "WARN"
    if health["live"]["status_code"] not in {200, 503}:
        status = "WARN"
    return {
        "report": "release_management_dashboard",
        "read_only": True,
        "status": status,
        "environment": env.get("app_env"),
        "version": version.get("version"),
        "migration_status": migration.get("status"),
        "health_status": health["health"]["payload"].get("status"),
        "notes_count": len(release_notes().get("notes", [])),
    }


def release_management_readiness_report() -> dict[str, Any]:
    dashboard = dashboard_payload()
    return {
        "generated_at": datetime.utcnow().isoformat(),
        "phase": "5.7",
        "sprint": "Release Management",
        "platform": dashboard["platform"],
        "status": dashboard["status"],
        "summary": dashboard["summary"],
        "features": list(FEATURES),
        "sections": {
            "environment": release_environment(),
            "version": release_version(),
            "release_notes": release_notes(),
            "migration": migration_status(),
            "health": release_health(),
            "rollback": release_rollback(),
        },
    }


def dashboard_payload() -> dict[str, Any]:
    ensure_release_management()
    dash = release_management_dashboard()
    env = release_environment()
    version = release_version()
    migration = migration_status()
    health = release_health()
    return {
        "platform": "Release Management",
        "phase": "5.7",
        "sprint": "Release Management",
        "status": dash["status"],
        "read_only": True,
        "generated_at": datetime.utcnow().isoformat(),
        "summary": {
            "environment": env.get("app_env"),
            "runtime_profile": env.get("runtime_profile"),
            "version": version.get("version"),
            "git_sha": version.get("git_sha"),
            "migration_status": migration.get("status"),
            "migration_checks_passed": migration.get("checks_passed", 0),
            "health_status": health["health"]["payload"].get("status"),
            "release_notes_count": len(release_notes().get("notes", [])),
        },
        "features": list(FEATURES),
    }
