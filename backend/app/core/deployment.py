import logging

from app.core.build_info import build_info
from app.core.config_validation import config_summary, validate_config

logger = logging.getLogger("dxcon.deployment")


def log_production_startup(app):
    info = build_info()
    summary = config_summary(app)

    logger.info(
        "dxcon production startup",
        extra={
            "event": "startup",
            "version": info["version"],
            "git_sha": info["git_sha"],
            "environment": info["environment"],
            "database_configured": summary["database_configured"],
        },
    )


def validate_startup(app):
    validate_config(app)

    migration_status = {"ready": True, "skipped": True}
    if app.config.get("STARTUP_VALIDATE_DB", True):
        try:
            from app.core.database_startup import startup_database_check

            migration_status = startup_database_check(app)
        except Exception as exc:
            migration_status = {"ready": False, "error": str(exc)}
            if app.config.get("APP_ENV") == "production":
                raise

    app.extensions.setdefault("dxcon_deployment", {})
    app.extensions["dxcon_deployment"]["migration_status"] = migration_status
    app.extensions["dxcon_deployment"]["startup_complete"] = True

    if app.config.get("APP_ENV") == "production":
        log_production_startup(app)

    return migration_status


def init_deployment(app):
    if app.config.get("TESTING"):
        app.extensions.setdefault("dxcon_deployment", {})
        app.extensions["dxcon_deployment"]["migration_status"] = {"ready": True, "testing": True}
        app.extensions["dxcon_deployment"]["startup_complete"] = True
        return {"ready": True, "testing": True}

    return validate_startup(app)


def deployment_readiness(app):
    checks = []
    score = 100

    try:
        validate_config(app)
        checks.append({"name": "config_validation", "status": "pass"})
    except Exception as exc:
        checks.append({"name": "config_validation", "status": "fail", "detail": str(exc)})
        score -= 25

    migration = app.extensions.get("dxcon_deployment", {}).get("migration_status")
    if migration and migration.get("ready"):
        checks.append({"name": "database_migrations", "status": "pass"})
    else:
        checks.append({"name": "database_migrations", "status": "warn", "detail": migration})
        score -= 15

    summary = config_summary(app)
    if summary.get("database_configured"):
        checks.append({"name": "database_configured", "status": "pass"})
    else:
        checks.append({"name": "database_configured", "status": "fail"})
        score -= 20

    if summary.get("secret_key_from_env") or app.config.get("APP_ENV") != "production":
        checks.append({"name": "secret_key", "status": "pass"})
    else:
        checks.append({"name": "secret_key", "status": "fail"})
        score -= 15

    if summary.get("jwt_secret_from_env") or app.config.get("APP_ENV") != "production":
        checks.append({"name": "jwt_secret", "status": "pass"})
    else:
        checks.append({"name": "jwt_secret", "status": "fail"})
        score -= 15

    engine_options = app.config.get("SQLALCHEMY_ENGINE_OPTIONS") or {}
    if engine_options:
        checks.append({"name": "connection_pool", "status": "pass"})
    else:
        checks.append({"name": "connection_pool", "status": "warn"})
        score -= 10

    score = max(score, 0)
    return {
        "score": score,
        "ready_for_production": score >= 80,
        "checks": checks,
        "build": build_info(),
    }
