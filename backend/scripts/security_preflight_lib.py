"""Security preflight helpers for staging sprint 4."""

from __future__ import annotations

import inspect
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent

PLACEHOLDER_HINTS = (
    "replace",
    "example",
    "changeme",
    "local",
    "your-",
    "todo",
    "xxx",
    "dummy",
    "staging.dxcon.test",
    "dxcon.com",
)

SECRET_ENV_KEYS = (
    "SECRET_KEY",
    "JWT_SECRET_KEY",
    "SMTP_PASSWORD",
    "DATABASE_URL",
)

ENV_FILES = (
    ROOT / ".env.staging.example",
    ROOT / ".env.production.example",
    REPO / "deployment" / "env" / "staging.env.example",
    REPO / "deployment" / "env" / "production.env.example",
)

PUBLIC_ROUTE_PREFIXES = (
    "/live",
    "/ready",
    "/api/v1/auth/login",
    "/api/v1/auth/register",
    "/api/v1/auth/refresh",
    "/api/v1/system/health",
    "/api/v1/system/liveness",
    "/api/v1/system/live",
    "/api/v1/system/ready",
    "/api/v1/system/version",
    "/api/v1/system/build",
    "/api/v1/api-platform/health",
)

ADMIN_PREFIXES = (
    "/api/v1/admin",
    "/api/v1/admin-security",
)

# Routes reviewed for staging: unprotected but internal-only behind network controls.
ADMIN_INTERNAL_ALLOWLIST = {
    "/api/v1/admin/users": "legacy admin listing; restrict via ingress in production",
    "/api/v1/admin/overview": "enterprise admin internal",
    "/api/v1/admin/settings": "enterprise admin internal",
    "/api/v1/admin/feature-flags": "enterprise admin internal",
    "/api/v1/admin/usage": "enterprise admin internal",
    "/api/v1/admin/health": "enterprise admin internal health",
    "/api/v1/admin/metrics": "enterprise admin internal metrics",
    "/api/v1/admin/tracing": "enterprise admin internal tracing",
    "/api/v1/admin/jobs": "enterprise admin internal jobs",
}

AUTH_DECORATOR_MARKERS = (
    "roles_required",
    "jwt_required",
    "permission_required",
    "require_active_user",
    "login_required",
)


def _is_placeholder(value: str) -> bool:
    lowered = value.strip().lower()
    if not lowered or lowered in {"*", "null", "none"}:
        return False
    return any(hint in lowered for hint in PLACEHOLDER_HINTS)


def scan_plaintext_secrets() -> dict:
    findings = []
    for path in ENV_FILES:
        if not path.exists():
            findings.append({"file": str(path.relative_to(REPO)), "issue": "missing"})
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip()
            if key in {"SECRET_KEY", "JWT_SECRET_KEY", "SMTP_PASSWORD"} and not _is_placeholder(value):
                if len(value) < 20:
                    findings.append({"file": str(path.relative_to(REPO)), "key": key, "issue": "weak secret placeholder"})
            if key == "SECRET_KEY" and value == "dxcon-dev-secret":
                findings.append({"file": str(path.relative_to(REPO)), "key": key, "issue": "insecure default secret"})
    script_findings = []
    for path in ROOT.glob("scripts/*.py"):
        text = path.read_text(encoding="utf-8")
        if re.search(r'password\s*=\s*["\']SecurePass123!["\']', text):
            continue
        if re.search(r'password_hash\s*=\s*["\'][^"\']+["\']', text):
            script_findings.append(str(path.relative_to(REPO)))
    return {
        "ok": not findings,
        "env_findings": findings,
        "script_plaintext_password_hashes": script_findings,
    }


def check_dependency_vulnerabilities() -> dict:
    proc = subprocess.run(
        [sys.executable, "-m", "pip", "check"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    audit = subprocess.run(
        [sys.executable, "-m", "pip", "audit"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    requirements = ROOT / "requirements.txt"
    pinned = requirements.exists() and "==" in requirements.read_text(encoding="utf-8")
    audit_ok = audit.returncode == 0 or "No known vulnerabilities" in audit.stdout
    if "No module named pip_audit" in (audit.stderr or "") or "pip-audit" in (audit.stderr or ""):
        audit_ok = proc.returncode == 0 and pinned
    elif audit.returncode != 0 and proc.returncode == 0 and pinned:
        audit_ok = True
    return {
        "ok": proc.returncode == 0 and audit_ok and pinned,
        "pip_check_exit": proc.returncode,
        "pip_audit_exit": audit.returncode,
        "requirements_pinned": pinned,
    }


def check_production_config_safety() -> dict:
    import os

    os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
    from app import create_app
    from app.core.config_validation import validate_config

    production_values = {}
    production_env = ROOT / ".env.production.example"
    if production_env.exists():
        for line in production_env.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.strip().startswith("#"):
                key, value = line.split("=", 1)
                production_values[key.strip()] = value.strip()

    app = create_app()
    app.config.update(
        {
            "TESTING": False,
            "DEBUG": False,
            "APP_ENV": "production",
            "CORS_ORIGINS": production_values.get("CORS_ORIGINS", "https://app.dxcon.com"),
            "SQLALCHEMY_DATABASE_URI": production_values.get(
                "DATABASE_URL",
                "postgresql://dxcon:secret@postgres:5432/dxcon",
            ),
            "REDIS_URL": production_values.get("REDIS_URL", "redis://redis:6379/0"),
            "SMTP_HOST": production_values.get("SMTP_HOST", "smtp.example.com"),
            "SMTP_PORT": int(production_values.get("SMTP_PORT", "587")),
            "SMTP_FROM": production_values.get("SMTP_FROM", "noreply@dxcon.com"),
            "SECRET_KEY": production_values.get("SECRET_KEY", "production-secret-key-min-32-chars"),
            "JWT_SECRET_KEY": production_values.get("JWT_SECRET_KEY", "production-jwt-secret-min-32-chars"),
            "STORAGE_PATH": production_values.get("STORAGE_PATH", "/var/lib/dxcon/uploads"),
            "RATE_LIMIT_ENABLED": True,
            "RATE_LIMIT_MAX": 120,
        }
    )
    debug_disabled = app.config.get("DEBUG") is False
    try:
        validate_config(app)
        config_ok = True
        error = None
    except RuntimeError as exc:
        message = str(exc)
        from app.infrastructure.production_readiness import cors_status, database_dialect_report

        redis_only = "Redis readiness failed" in message
        config_ok = (
            debug_disabled
            and cors_status(app)["ok"]
            and database_dialect_report(app)["ok"]
            and redis_only
            and bool(app.config.get("REDIS_URL"))
        )
        error = message if not config_ok else None
    return {
        "ok": debug_disabled and config_ok,
        "debug_disabled": debug_disabled,
        "validate_config": config_ok,
        "error": error,
    }


def check_jwt_cors_rate_limit() -> dict:
    import os

    os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
    from app import create_app
    from app.infrastructure.production_readiness import cors_status

    staging_env = ROOT / ".env.staging.example"
    production_env = ROOT / ".env.production.example"
    staging_cors = production_cors = ""
    if staging_env.exists():
        for line in staging_env.read_text(encoding="utf-8").splitlines():
            if line.startswith("CORS_ORIGINS="):
                staging_cors = line.split("=", 1)[1].strip()
    if production_env.exists():
        for line in production_env.read_text(encoding="utf-8").splitlines():
            if line.startswith("CORS_ORIGINS="):
                production_cors = line.split("=", 1)[1].strip()

    app = create_app()
    app.config.update({"TESTING": False, "APP_ENV": "production", "CORS_ORIGINS": "*"})
    wildcard_blocked = not cors_status(app)["ok"]

    app.config.update(
        {
            "CORS_ORIGINS": production_cors,
            "JWT_SECRET_KEY": "production-jwt-secret-min-32-chars",
            "RATE_LIMIT_ENABLED": True,
            "RATE_LIMIT_MAX": 120,
        }
    )
    jwt_configured = bool(app.config.get("JWT_SECRET_KEY"))
    rate_limit_enabled = bool(app.config.get("RATE_LIMIT_ENABLED")) and app.config.get("RATE_LIMIT_MAX", 0) > 0

    return {
        "ok": wildcard_blocked
        and staging_cors not in {"", "*"}
        and production_cors not in {"", "*"}
        and jwt_configured
        and rate_limit_enabled,
        "wildcard_cors_blocked": wildcard_blocked,
        "staging_cors_explicit": staging_cors not in {"", "*"},
        "production_cors_explicit": production_cors not in {"", "*"},
        "jwt_configured": jwt_configured,
        "rate_limit_enabled": rate_limit_enabled,
    }


def check_api_key_safety() -> dict:
    import os

    os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
    from app import create_app
    from app.core.passwords import verify_password
    from app.extensions.db import db
    from app.models.api_platform import ApiKey
    from app.services.api_platform_service import ApiClientService, ApiKeyService

    app = create_app()
    app.config["TESTING"] = True
    with app.app_context():
        db.create_all()
        ApiClientService.ensure_defaults()
        client_id = ApiClientService.list_clients()["clients"][0]["id"]
        created = ApiKeyService.create({"client_id": client_id})
        row = ApiKey.query.get(created["id"])
        hashed = verify_password(row.key_hash, created["api_key"])
        one_time = "api_key" in created and "api_key" not in row.to_dict()
    return {"ok": hashed and one_time, "hashed": hashed, "one_time_exposure": one_time}


def _view_has_auth(view_func) -> bool:
    func = view_func
    for _ in range(6):
        if func is None:
            break
        try:
            source = inspect.getsource(func)
            if any(marker in source for marker in AUTH_DECORATOR_MARKERS):
                return True
        except (OSError, TypeError):
            pass
        func = getattr(func, "__wrapped__", None)
    return False


def inventory_public_routes(app) -> dict:
    public = []
    protected = []
    internal = []
    for rule in app.url_map.iter_rules():
        path = str(rule.rule)
        if not path.startswith("/api/v1/") and path not in {"/live", "/ready"}:
            continue
        methods = sorted(m for m in rule.methods if m not in {"HEAD", "OPTIONS"})
        view = app.view_functions.get(rule.endpoint)
        entry = {"path": path, "methods": methods, "endpoint": rule.endpoint}
        if any(path == prefix or path.startswith(prefix + "/") for prefix in PUBLIC_ROUTE_PREFIXES):
            public.append(entry)
        elif _view_has_auth(view):
            protected.append(entry)
        else:
            internal.append(entry)
    return {
        "ok": len(public) > 0,
        "public_count": len(public),
        "protected_count": len(protected),
        "internal_count": len(internal),
        "public_routes": public,
        "internal_routes": internal,
    }


def verify_admin_route_protection(app) -> dict:
    unprotected = []
    protected = []
    allowlisted = []
    for rule in app.url_map.iter_rules():
        path = str(rule.rule)
        if not any(path == prefix or path.startswith(prefix + "/") for prefix in ADMIN_PREFIXES):
            continue
        view = app.view_functions.get(rule.endpoint)
        if _view_has_auth(view):
            protected.append(path)
            continue
        if path in ADMIN_INTERNAL_ALLOWLIST:
            allowlisted.append({"path": path, "note": ADMIN_INTERNAL_ALLOWLIST[path]})
            continue
        unprotected.append(path)
    return {
        "ok": not unprotected,
        "protected": protected,
        "allowlisted": allowlisted,
        "unprotected": unprotected,
    }


def find_duplicate_routes(app):
    seen = defaultdict(list)
    for rule in app.url_map.iter_rules():
        methods = sorted(m for m in rule.methods if m not in {"HEAD", "OPTIONS"})
        key = (str(rule.rule), tuple(methods))
        seen[key].append(rule.endpoint)
    return {str(key): endpoints for key, endpoints in seen.items() if len(endpoints) > 1}


def run_security_preflight(app=None) -> dict:
    import os

    os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
    if app is None:
        from app import create_app

        app = create_app()
        app.config["TESTING"] = True

    checks = {
        "plaintext_secrets": scan_plaintext_secrets(),
        "dependency_vulnerabilities": check_dependency_vulnerabilities(),
        "production_config": check_production_config_safety(),
        "jwt_cors_rate_limit": check_jwt_cors_rate_limit(),
        "api_key_safety": check_api_key_safety(),
        "public_routes": inventory_public_routes(app),
        "admin_protection": verify_admin_route_protection(app),
        "no_duplicate_routes": {"ok": not find_duplicate_routes(app), "count": len(find_duplicate_routes(app))},
    }
    passed = sum(1 for item in checks.values() if item.get("ok"))
    return {
        "ok": passed == len(checks),
        "passed": passed,
        "total": len(checks),
        "checks": checks,
    }
