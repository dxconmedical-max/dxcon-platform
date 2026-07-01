"""Staging deployment stack validation helpers."""

from __future__ import annotations

import subprocess
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent

REQUIRED_ENV_KEYS = (
    "DATABASE_URL",
    "REDIS_URL",
    "SECRET_KEY",
    "JWT_SECRET_KEY",
    "CORS_ORIGINS",
    "SMTP_HOST",
    "STORAGE_PATH",
)

DOCKER_FILES = (
    REPO / "backend" / "Dockerfile",
    REPO / "docker-compose.staging.yml",
    REPO / "docker-compose.production.yml",
    ROOT / "gunicorn.conf.py",
    ROOT / "production_start.py",
)

NGINX_FILES = (
    REPO / "deployment" / "nginx" / "nginx.conf",
    REPO / "deployment" / "nginx" / "default.conf",
)

ENV_FILES = (
    ROOT / ".env.staging.example",
    ROOT / ".env.production.example",
    REPO / "deployment" / "env" / "staging.env.example",
    REPO / "deployment" / "env" / "production.env.example",
)

BACKUP_SCRIPTS = (
    REPO / "deployment" / "scripts" / "backup_postgres.sh",
    REPO / "deployment" / "scripts" / "restore_postgres_dry_run.sh",
    REPO / "deployment" / "scripts" / "backup_uploads.sh",
)

RC2_TAG = "v1.0.0-rc2"


def parse_env_file(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    values = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def validate_env_file(path: Path) -> dict:
    values = parse_env_file(path)
    missing = [key for key in REQUIRED_ENV_KEYS if not values.get(key)]
    cors = values.get("CORS_ORIGINS", "")
    database = values.get("DATABASE_URL", "")
    return {
        "ok": not missing and cors not in {"", "*"} and database.startswith("postgresql"),
        "missing": missing,
        "cors": cors,
        "database_url": database,
    }


def find_duplicate_routes(app):
    seen = defaultdict(list)
    for rule in app.url_map.iter_rules():
        methods = sorted(m for m in rule.methods if m not in {"HEAD", "OPTIONS"})
        key = (str(rule.rule), tuple(methods))
        seen[key].append(rule.endpoint)
    return {str(key): endpoints for key, endpoints in seen.items() if len(endpoints) > 1}


def verify_docker_stack() -> dict:
    missing = [str(path.relative_to(REPO)) for path in DOCKER_FILES if not path.exists()]
    staging = (REPO / "docker-compose.staging.yml").read_text(encoding="utf-8") if (REPO / "docker-compose.staging.yml").exists() else ""
    services = ["api:", "postgres:", "redis:", "nginx:", "worker:", "scheduler:"]
    missing_services = [name for name in services if name not in staging]
    dockerfile = (REPO / "backend" / "Dockerfile").read_text(encoding="utf-8") if (REPO / "backend" / "Dockerfile").exists() else ""
    hardened = "HEALTHCHECK" in dockerfile and "USER" in dockerfile and "production_start.py" in dockerfile
    return {
        "ok": not missing and not missing_services and hardened,
        "missing_files": missing,
        "missing_services": missing_services,
        "hardened": hardened,
    }


def verify_nginx_config() -> dict:
    missing = [str(path.relative_to(REPO)) for path in NGINX_FILES if not path.exists()]
    nginx_conf = NGINX_FILES[0].read_text(encoding="utf-8") if NGINX_FILES[0].exists() else ""
    default_conf = NGINX_FILES[1].read_text(encoding="utf-8") if NGINX_FILES[1].exists() else ""
    checks = {
        "gzip": "gzip on" in nginx_conf,
        "client_max_body_size": "client_max_body_size" in nginx_conf,
        "proxy_timeouts": "proxy_read_timeout" in nginx_conf,
        "health_route": "/live" in default_conf,
        "security_headers": "X-Content-Type-Options" in default_conf,
        "reverse_proxy": "proxy_pass" in default_conf,
    }
    return {"ok": not missing and all(checks.values()), "missing_files": missing, "checks": checks}


def verify_env_templates() -> dict:
    reports = {}
    for path in ENV_FILES:
        reports[str(path.relative_to(REPO))] = validate_env_file(path)
    ok = all(item["ok"] for item in reports.values()) and len(reports) == len(ENV_FILES)
    return {"ok": ok, "files": reports}


def verify_app_boot():
    import os

    os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
    from app import create_app
    from app.extensions.db import db

    app = create_app()
    app.config["TESTING"] = True
    with app.app_context():
        db.create_all()
    return {"ok": app is not None, "name": app.name}


def verify_health_routes():
    import os

    os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
    from app import create_app
    from app.extensions.db import db

    app = create_app()
    app.config["TESTING"] = True
    with app.app_context():
        db.create_all()
        client = app.test_client()
        paths = ["/live", "/ready", "/api/v1/system/health", "/api/v1/system/liveness"]
        statuses = {path: client.get(path).status_code for path in paths}
    ok = all(code in {200, 503} for code in statuses.values())
    return {"ok": ok, "status_codes": statuses}


def verify_staging_config():
    import os

    os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
    from app import create_app
    from app.infrastructure.production_readiness import database_dialect_report, evaluate_go_live_blockers

    staging_values = parse_env_file(ROOT / ".env.staging.example")
    app = create_app()
    app.config.update(
        {
            "TESTING": False,
            "APP_ENV": "staging",
            "CORS_ORIGINS": staging_values.get("CORS_ORIGINS", ""),
            "SQLALCHEMY_DATABASE_URI": staging_values.get("DATABASE_URL", ""),
            "REDIS_URL": staging_values.get("REDIS_URL", ""),
            "SMTP_HOST": staging_values.get("SMTP_HOST", ""),
            "SMTP_PORT": int(staging_values.get("SMTP_PORT", "587")),
            "SMTP_FROM": staging_values.get("SMTP_FROM", ""),
            "SECRET_KEY": staging_values.get("SECRET_KEY", "staging-secret"),
            "JWT_SECRET_KEY": staging_values.get("JWT_SECRET_KEY", "staging-jwt"),
        }
    )
    db_report = database_dialect_report(app)
    blockers = evaluate_go_live_blockers(app)
    return {
        "ok": db_report["ok"] and blockers["ready"],
        "database": db_report,
        "blockers": blockers["blockers"],
    }


def verify_production_guards():
    import os

    os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
    from app import create_app
    from app.infrastructure.production_readiness import cors_status, database_dialect_report, validate_database

    app = create_app()
    app.config.update(
        {
            "TESTING": False,
            "APP_ENV": "production",
            "CORS_ORIGINS": "*",
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        }
    )
    cors_blocked = not cors_status(app)["ok"]
    sqlite_blocked = not database_dialect_report(app)["ok"]
    raised = False
    try:
        validate_database(app)
    except RuntimeError:
        raised = True
    return {"ok": cors_blocked and sqlite_blocked and raised}


def verify_backup_scripts() -> dict:
    missing = [str(path.relative_to(REPO)) for path in BACKUP_SCRIPTS if not path.exists()]
    return {"ok": not missing, "missing": missing}


def verify_rc2_tag() -> dict:
    result = subprocess.run(
        ["git", "tag", "-l", RC2_TAG],
        cwd=str(REPO),
        capture_output=True,
        text=True,
        check=False,
    )
    tag_present = RC2_TAG in result.stdout.split()
    return {
        "ok": tag_present,
        "tag": RC2_TAG,
        "documented": "DxCon Platform v1.0.0 RC2 staging baseline",
        "present": tag_present,
    }


def verify_route_inventory():
    import os

    os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
    from app import create_app

    app = create_app()
    duplicates = find_duplicate_routes(app)
    return {"ok": not duplicates, "count": len(duplicates)}


def run_staging_verification() -> dict:
    checks = {
        "docker_stack": verify_docker_stack(),
        "nginx_config": verify_nginx_config(),
        "env_templates": verify_env_templates(),
        "app_boot": verify_app_boot(),
        "health_routes": verify_health_routes(),
        "staging_config": verify_staging_config(),
        "production_guards": verify_production_guards(),
        "backup_scripts": verify_backup_scripts(),
        "rc2_tag": verify_rc2_tag(),
        "route_inventory": verify_route_inventory(),
    }
    passed = sum(1 for item in checks.values() if item.get("ok"))
    return {
        "ok": passed == len(checks),
        "passed": passed,
        "total": len(checks),
        "checks": checks,
    }
