import logging
import os
from pathlib import Path

from app.core.build_info import build_info
from app.core.config_validation import config_summary

logger = logging.getLogger("dxcon.startup")


def check_storage(app):
    storage_path = app.config.get("STORAGE_PATH") or "uploads"
    path = Path(storage_path)
    try:
        path.mkdir(parents=True, exist_ok=True)
        test_file = path / ".startup_check"
        test_file.write_text("ok", encoding="utf-8")
        test_file.unlink(missing_ok=True)
        return {"name": "storage", "status": "pass", "path": str(path.resolve())}
    except Exception as exc:
        return {"name": "storage", "status": "fail", "detail": str(exc)}


def check_redis(app):
    redis_url = app.config.get("REDIS_URL")
    if not redis_url:
        return {"name": "redis", "status": "skipped", "detail": "REDIS_URL not configured"}
    try:
        import redis

        client = redis.from_url(redis_url, socket_connect_timeout=2)
        client.ping()
        return {"name": "redis", "status": "pass"}
    except ImportError:
        return {"name": "redis", "status": "warn", "detail": "redis package not installed"}
    except Exception as exc:
        return {"name": "redis", "status": "fail", "detail": str(exc)}


def check_smtp(app):
    host = app.config.get("SMTP_HOST")
    if not host:
        return {"name": "smtp", "status": "skipped", "detail": "SMTP_HOST not configured"}
    required = ["SMTP_HOST", "SMTP_PORT", "SMTP_FROM"]
    missing = [key for key in required if not app.config.get(key)]
    if missing:
        return {"name": "smtp", "status": "warn", "detail": f"missing: {', '.join(missing)}"}
    return {"name": "smtp", "status": "pass", "host": host}


def check_jwt(app):
    from app.core.config_validation import INSECURE_DEFAULTS

    env = (app.config.get("APP_ENV") or "development").lower()
    jwt_secret = app.config.get("JWT_SECRET_KEY")
    if env == "production" and jwt_secret == INSECURE_DEFAULTS["JWT_SECRET_KEY"]:
        return {"name": "jwt", "status": "fail", "detail": "JWT_SECRET_KEY must be overridden in production"}
    if app.config.get("JWT_ACCESS_TOKEN_EXPIRES") is None:
        return {"name": "jwt", "status": "fail", "detail": "JWT_ACCESS_TOKEN_EXPIRES not configured"}
    return {"name": "jwt", "status": "pass"}


def check_scheduler(app):
    from app.core.background_tasks import background_tasks

    stats = background_tasks.snapshot()
    return {
        "name": "scheduler",
        "status": "pass",
        "workers": app.config.get("BACKGROUND_TASK_WORKERS", 4),
        "stats": stats,
    }


def check_plugins(app):
    blueprints = sorted(app.blueprints.keys())
    api_v1_routes = [
        str(rule)
        for rule in app.url_map.iter_rules()
        if str(rule).startswith("/api/v1/")
    ]
    return {
        "name": "plugins",
        "status": "pass" if blueprints else "fail",
        "blueprint_count": len(blueprints),
        "api_v1_route_count": len(api_v1_routes),
    }


def run_startup_checks(app):
    checks = [
        check_storage(app),
        check_jwt(app),
        check_scheduler(app),
        check_plugins(app),
        check_smtp(app),
        check_redis(app),
    ]

    failed = [item for item in checks if item["status"] == "fail"]
    result = {
        "status": "OK" if not failed else "DEGRADED",
        "checks": checks,
        "build": build_info(),
        "config": config_summary(app),
    }

    logger.info("startup checks completed", extra={"status": result["status"], "failed": len(failed)})
    app.extensions.setdefault("dxcon_startup", {})
    app.extensions["dxcon_startup"]["checks"] = result
    return result
