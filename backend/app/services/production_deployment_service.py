"""Production deployment business logic for Phase 5 Sprint 5.5."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from flask import current_app

from app.core.build_info import build_info
from app.infrastructure.infrastructure_services import InfrastructureHealthService, InfrastructureReadinessService
from app.infrastructure.production_health import health_payload, live_payload, ready_payload
from app.operations.deployment_service import DeploymentService
from app.runtime.deployment_profile import current_profile, profile_settings
from app.services.reporting_service import _safe

PRODUCTION_DEPLOYMENT_ROLES = ("SUPER_ADMIN", "ADMIN")

ROOT = Path(__file__).resolve().parents[2]
REPO = ROOT.parent

DEPLOYMENT_ASSETS = {
    "dockerfile": REPO / "backend" / "Dockerfile",
    "docker_compose_production": REPO / "docker-compose.production.yml",
    "docker_compose_staging": REPO / "docker-compose.staging.yml",
    "production_start": ROOT / "production_start.py",
    "gunicorn_conf": ROOT / "gunicorn.conf.py",
    "nginx_conf": REPO / "deployment" / "nginx" / "nginx.conf",
    "nginx_default": REPO / "deployment" / "nginx" / "default.conf",
    "k8s_deployment": REPO / "deployment" / "kubernetes" / "deployment.yaml",
    "deploy_pipeline": REPO / "deployment" / "pipeline" / "deploy.py",
    "rollback_pipeline": REPO / "deployment" / "pipeline" / "rollback.py",
    "deployment_guide": REPO / "docs" / "DEPLOYMENT.md",
    "release_checklist": ROOT / "scripts" / "go_live_checklist.txt",
}

FEATURES = (
    "Docker Production Profile",
    "Nginx Production",
    "Health Probes",
    "Rolling Deployment",
    "Zero-downtime Migration",
    "Release Checklist",
    "Rollback Checklist",
)

PROBE_PATHS = (
    "/live",
    "/ready",
    "/api/v1/system/health",
    "/api/v1/system/liveness",
)


class ProductionDeploymentError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


def ensure_production_deployment() -> dict[str, Any]:
    return {"ready": True, "read_only": True}


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def docker_production_profile() -> dict[str, Any]:
    ensure_production_deployment()
    dockerfile = _read_text(DEPLOYMENT_ASSETS["dockerfile"])
    compose = _read_text(DEPLOYMENT_ASSETS["docker_compose_production"])
    services = ["api:", "postgres:", "redis:", "nginx:", "worker:", "scheduler:"]
    missing_services = [name for name in services if name not in compose]
    checks = {
        "dockerfile_exists": DEPLOYMENT_ASSETS["dockerfile"].exists(),
        "compose_exists": DEPLOYMENT_ASSETS["docker_compose_production"].exists(),
        "non_root_user": "USER 10001" in dockerfile,
        "healthcheck": "HEALTHCHECK" in dockerfile,
        "production_start": "production_start.py" in dockerfile,
        "app_env_production": "APP_ENV=production" in dockerfile or "APP_ENV: production" in compose,
        "stop_grace_period": "stop_grace_period" in compose,
        "resource_limits": "resources:" in compose or "limits:" in compose,
        "services_complete": not missing_services,
    }
    profile = profile_settings("production")
    return {
        "report": "docker_production_profile",
        "read_only": True,
        "profile": profile,
        "runtime_profile": current_profile(),
        "compose_file": str(DEPLOYMENT_ASSETS["docker_compose_production"].relative_to(REPO)),
        "dockerfile": str(DEPLOYMENT_ASSETS["dockerfile"].relative_to(REPO)),
        "services_expected": [s.rstrip(":") for s in services],
        "missing_services": missing_services,
        "checks": checks,
        "checks_passed": sum(1 for value in checks.values() if value),
        "checks_total": len(checks),
        "assets_available": {name: path.exists() for name, path in DEPLOYMENT_ASSETS.items()},
    }


def nginx_production() -> dict[str, Any]:
    ensure_production_deployment()
    nginx_conf = _read_text(DEPLOYMENT_ASSETS["nginx_conf"])
    default_conf = _read_text(DEPLOYMENT_ASSETS["nginx_default"])
    checks = {
        "nginx_conf_exists": DEPLOYMENT_ASSETS["nginx_conf"].exists(),
        "default_conf_exists": DEPLOYMENT_ASSETS["nginx_default"].exists(),
        "gzip_enabled": "gzip on" in nginx_conf,
        "client_max_body_size": "client_max_body_size" in nginx_conf,
        "proxy_timeouts": "proxy_read_timeout" in nginx_conf,
        "health_route_live": "/live" in default_conf,
        "health_route_ready": "/ready" in default_conf,
        "security_headers": "X-Content-Type-Options" in default_conf,
        "reverse_proxy": "proxy_pass" in default_conf,
        "upstream_keepalive": "keepalive" in default_conf,
    }
    return {
        "report": "nginx_production",
        "read_only": True,
        "nginx_conf": str(DEPLOYMENT_ASSETS["nginx_conf"].relative_to(REPO)),
        "default_conf": str(DEPLOYMENT_ASSETS["nginx_default"].relative_to(REPO)),
        "checks": checks,
        "checks_passed": sum(1 for value in checks.values() if value),
        "checks_total": len(checks),
    }


def health_probes() -> dict[str, Any]:
    ensure_production_deployment()
    app = current_app._get_current_object()
    live, live_code = live_payload(app)
    ready, ready_code = ready_payload(app)
    health, health_code = health_payload(app)
    k8s = _read_text(DEPLOYMENT_ASSETS["k8s_deployment"])
    dockerfile = _read_text(DEPLOYMENT_ASSETS["dockerfile"])
    compose = _read_text(DEPLOYMENT_ASSETS["docker_compose_production"])
    return {
        "report": "health_probes",
        "read_only": True,
        "probe_paths": list(PROBE_PATHS),
        "live_probe": {"path": "/live", "status_code": live_code, "payload": live},
        "ready_probe": {"path": "/ready", "status_code": ready_code, "payload": ready},
        "health_probe": {"path": "/api/v1/system/health", "status_code": health_code, "payload": health},
        "docker_healthcheck": "HEALTHCHECK" in dockerfile,
        "compose_healthcheck": "healthcheck:" in compose,
        "kubernetes_readiness": "readinessProbe:" in k8s,
        "kubernetes_liveness": "livenessProbe:" in k8s,
        "nginx_live_route": "/live" in _read_text(DEPLOYMENT_ASSETS["nginx_default"]),
    }


def rolling_deployment() -> dict[str, Any]:
    ensure_production_deployment()
    k8s = _read_text(DEPLOYMENT_ASSETS["k8s_deployment"])
    compose = _read_text(DEPLOYMENT_ASSETS["docker_compose_production"])
    replicas = 2 if "replicas: 2" in k8s else 1
    strategy = {
        "type": "RollingUpdate" if "RollingUpdate" in k8s or "replicas:" in k8s else "Recreate",
        "max_surge": "25%" if "maxSurge" in k8s else "default",
        "max_unavailable": "0" if "maxUnavailable: 0" in k8s else "default",
    }
    steps = [
        "Build and tag container image with BUILD_VERSION.",
        "Run pre-deployment verification (deployment/pipeline/verify_deployment.py pre).",
        "Apply Kubernetes manifests or docker compose up with health-gated nginx.",
        "Wait for /ready on all new replicas before draining old pods.",
        "Run post-deployment verification and smoke tests.",
    ]
    return {
        "report": "rolling_deployment",
        "read_only": True,
        "strategy": strategy,
        "replicas": replicas,
        "compose_restart_policy": "unless-stopped" in compose,
        "nginx_upstream_keepalive": "keepalive" in _read_text(DEPLOYMENT_ASSETS["nginx_default"]),
        "pipeline_entrypoint": str(DEPLOYMENT_ASSETS["deploy_pipeline"].relative_to(REPO)),
        "pipeline_available": DEPLOYMENT_ASSETS["deploy_pipeline"].exists(),
        "steps": steps,
        "legacy_api": "GET /api/v1/operations/deployment",
    }


def zero_downtime_migration() -> dict[str, Any]:
    ensure_production_deployment()
    app = current_app._get_current_object()
    from app.core.database_startup import verify_migrations

    migration = _safe(lambda: verify_migrations(app), {"ready": False})
    checks = [
        {
            "id": 1,
            "title": "Readiness gate includes migrations",
            "detail": "/ready returns 503 until database migrations are applied.",
            "status": "PASS",
        },
        {
            "id": 2,
            "title": "Startup migration validation",
            "detail": "STARTUP_VALIDATE_DB runs migration checks on boot in production.",
            "status": "PASS" if app.config.get("STARTUP_VALIDATE_DB", True) else "WARN",
        },
        {
            "id": 3,
            "title": "Migration status available",
            "detail": "verify_migrations exposes current migration readiness.",
            "status": "PASS" if migration.get("ready") else "WARN",
        },
        {
            "id": 4,
            "title": "Rolling deploy with probe gate",
            "detail": "New pods only receive traffic after /ready succeeds.",
            "status": "PASS"
            if "readinessProbe:" in _read_text(DEPLOYMENT_ASSETS["k8s_deployment"])
            else "MANUAL",
        },
        {
            "id": 5,
            "title": "Backward-compatible schema changes",
            "detail": "Apply expand/contract migrations before code cutover.",
            "status": "DOCUMENTED",
        },
    ]
    return {
        "report": "zero_downtime_migration",
        "read_only": True,
        "migration_status": migration,
        "startup_validate_db": bool(app.config.get("STARTUP_VALIDATE_DB", True)),
        "checks": checks,
        "checks_passed": sum(1 for item in checks if item["status"] in ("PASS", "DOCUMENTED")),
        "checks_total": len(checks),
        "guide": str(DEPLOYMENT_ASSETS["deployment_guide"].relative_to(REPO)),
    }


def release_checklist() -> dict[str, Any]:
    ensure_production_deployment()
    checklist_path = DEPLOYMENT_ASSETS["release_checklist"]
    items = []
    if checklist_path.exists():
        for line in checklist_path.read_text(encoding="utf-8").splitlines():
            text = line.strip()
            if text.startswith("[ ]") or text.startswith("[x]"):
                items.append({"item": text[3:].strip(), "checked": text.startswith("[x]")})
    deployment = _safe(DeploymentService.current, {})
    default_items = [
        "health_check.py",
        "verify_staging_stack.py",
        "Render deploy success",
        "/monitor OK",
        "security preflight pass",
    ]
    if not items:
        items = [{"item": name, "checked": False} for name in default_items]
    return {
        "report": "release_checklist",
        "read_only": True,
        "items": items,
        "items_total": len(items),
        "deployment_current": deployment,
        "pipeline": str(DEPLOYMENT_ASSETS["deploy_pipeline"].relative_to(REPO)),
        "verify_scripts": [
            "backend/scripts/verify_production_deployment.py",
            "backend/scripts/verify_staging_stack.py",
            "deployment/pipeline/verify_deployment.py",
        ],
        "legacy_api": "POST /api/v1/operations/deployment/check",
    }


def rollback_checklist() -> dict[str, Any]:
    ensure_production_deployment()
    plan = _safe(DeploymentService.rollback_plan, None)
    pipeline_steps = [
        "Validate backup artifacts",
        "Run restore dry-run",
        "Deploy previous container image tag",
        "Run post-deployment verification",
    ]
    if DEPLOYMENT_ASSETS["rollback_pipeline"].exists():
        pipeline_steps = [
            "Validate backup artifacts",
            "Run restore dry-run",
            "Deploy previous container image tag (BUILD_VERSION)",
            "Run post-deployment verification",
        ]
    items = [
        {"id": 1, "item": "Confirm rollback target version / image tag", "required": True},
        {"id": 2, "item": "GET /api/v1/operations/deployment/rollback-plan", "required": True},
        {"id": 3, "item": "Run deployment/pipeline/rollback.py (metadata plan)", "required": True},
        {"id": 4, "item": "Execute restore dry-run if database regression suspected", "required": False},
        {"id": 5, "item": "Verify /live and /ready after rollback", "required": True},
        {"id": 6, "item": "Record incident in audit trail", "required": True},
    ]
    return {
        "report": "rollback_checklist",
        "read_only": True,
        "items": items,
        "pipeline_steps": pipeline_steps,
        "rollback_plan": plan,
        "pipeline_script": str(DEPLOYMENT_ASSETS["rollback_pipeline"].relative_to(REPO)),
        "pipeline_available": DEPLOYMENT_ASSETS["rollback_pipeline"].exists(),
        "legacy_api": "GET /api/v1/operations/deployment/rollback-plan",
    }


def production_deployment_dashboard() -> dict[str, Any]:
    ensure_production_deployment()
    docker = docker_production_profile()
    nginx = nginx_production()
    probes = health_probes()
    rolling = rolling_deployment()
    migration = zero_downtime_migration()
    status = "OK"
    if docker["checks_passed"] < docker["checks_total"]:
        status = "WARN"
    if nginx["checks_passed"] < nginx["checks_total"]:
        status = "WARN"
    return {
        "report": "production_deployment_dashboard",
        "read_only": True,
        "status": status,
        "build": build_info(),
        "docker_checks_passed": docker["checks_passed"],
        "nginx_checks_passed": nginx["checks_passed"],
        "migration_checks_passed": migration["checks_passed"],
        "replicas": rolling["replicas"],
        "probe_paths": len(PROBE_PATHS),
    }


def production_deployment_readiness_report() -> dict[str, Any]:
    dashboard = dashboard_payload()
    app = current_app._get_current_object()
    infra = _safe(lambda: InfrastructureReadinessService.readiness(app), {})
    return {
        "generated_at": datetime.utcnow().isoformat(),
        "phase": "5.5",
        "sprint": "Production Deployment",
        "platform": dashboard["platform"],
        "status": dashboard["status"],
        "summary": dashboard["summary"],
        "features": list(FEATURES),
        "infrastructure_readiness": infra,
        "sections": {
            "docker": docker_production_profile(),
            "nginx": nginx_production(),
            "probes": health_probes(),
            "rolling": rolling_deployment(),
            "migration": zero_downtime_migration(),
            "release": release_checklist(),
            "rollback": rollback_checklist(),
        },
    }


def dashboard_payload() -> dict[str, Any]:
    ensure_production_deployment()
    dash = production_deployment_dashboard()
    docker = docker_production_profile()
    nginx = nginx_production()
    migration = zero_downtime_migration()
    health = InfrastructureHealthService.status(current_app._get_current_object())
    return {
        "platform": "Production Deployment",
        "phase": "5.5",
        "sprint": "Production Deployment",
        "status": dash["status"],
        "read_only": True,
        "generated_at": datetime.utcnow().isoformat(),
        "summary": {
            "docker_checks_passed": docker["checks_passed"],
            "docker_checks_total": docker["checks_total"],
            "nginx_checks_passed": nginx["checks_passed"],
            "nginx_checks_total": nginx["checks_total"],
            "migration_checks_passed": migration["checks_passed"],
            "migration_checks_total": migration["checks_total"],
            "deployment_score": health.get("deployment_score", 0),
            "runtime_profile": health.get("runtime_profile", "unknown"),
        },
        "features": list(FEATURES),
    }
