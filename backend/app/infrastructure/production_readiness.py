"""Production go-live blocker validation for Release 4.9."""

from __future__ import annotations

from datetime import datetime, timezone


STRICT_ENVS = {"production", "prod", "live", "staging", "stage", "uat"}
RELAXED_ENVS = {"development", "testing", "test", "ci"}


def app_env(app):
    return (app.config.get("APP_ENV") or "development").lower()


def is_production(app):
    return app_env(app) in {"production", "prod", "live"}


def is_staging(app):
    return app_env(app) in {"staging", "stage", "uat"}


def is_strict_env(app):
    return app_env(app) in STRICT_ENVS


def is_relaxed_env(app):
    return app_env(app) in RELAXED_ENVS or bool(app.config.get("TESTING"))


def validate_cors(app):
    origins = (app.config.get("CORS_ORIGINS") or "*").strip()
    if is_strict_env(app) and (origins == "*" or not origins):
        raise RuntimeError("CORS_ORIGINS must be explicit in staging/production")
    return True


def cors_status(app):
    origins = (app.config.get("CORS_ORIGINS") or "*").strip()
    strict = is_strict_env(app)
    safe = not strict or (origins != "*" and bool(origins))
    return {
        "ok": safe,
        "origins": origins,
        "strict_env": strict,
        "wildcard_allowed": is_relaxed_env(app),
    }


def database_dialect_report(app):
    uri = app.config.get("SQLALCHEMY_DATABASE_URI") or ""
    dialect = uri.split(":", 1)[0] if uri else "unknown"
    sqlite = dialect == "sqlite"
    blocked = is_strict_env(app) and sqlite
    return {
        "dialect": dialect,
        "configured": bool(uri),
        "sqlite": sqlite,
        "sqlite_blocked_in_env": blocked,
        "postgresql_expected": is_strict_env(app),
        "ok": not blocked,
    }


def validate_database(app):
    report = database_dialect_report(app)
    if report["sqlite_blocked_in_env"]:
        raise RuntimeError("SQLite DATABASE_URL is not allowed in staging/production")
    if is_strict_env(app) and report["dialect"] not in {"postgresql", "postgres"}:
        raise RuntimeError("DATABASE_URL must use PostgreSQL in staging/production")
    if not report["configured"]:
        raise RuntimeError("DATABASE_URL must be configured")
    return True


def check_redis_health(app):
    url = (app.config.get("REDIS_URL") or "").strip()
    required = is_production(app)
    if not url:
        if required:
            return {"status": "DOWN", "required": True, "mode": "missing", "ok": False}
        return {"status": "DEGRADED", "required": False, "mode": "not_configured", "ok": True}

    try:
        import redis

        client = redis.from_url(url, socket_connect_timeout=2)
        client.ping()
        return {"status": "OK", "required": required, "mode": "connected", "ok": True}
    except ImportError:
        payload = {
            "status": "DOWN" if required else "DEGRADED",
            "required": required,
            "mode": "package_missing",
            "ok": not required,
        }
        return payload
    except Exception as exc:
        return {
            "status": "DOWN" if required else "DEGRADED",
            "required": required,
            "mode": "unavailable",
            "error": str(exc),
            "ok": not required,
        }


def validate_redis(app):
    if is_production(app) and not (app.config.get("REDIS_URL") or "").strip():
        raise RuntimeError("REDIS_URL is required in production")
    health = check_redis_health(app)
    if is_production(app) and not health.get("ok"):
        detail = health.get("error") or health.get("mode") or "unavailable"
        raise RuntimeError(f"Redis readiness failed in production: {detail}")
    return True


def check_smtp_readiness(app):
    host = (app.config.get("SMTP_HOST") or "").strip()
    if not host:
        blocker = is_production(app)
        return {
            "status": "WARNING" if blocker else "DEGRADED",
            "blocker": blocker,
            "mode": "not_configured",
            "ok": not blocker,
        }

    missing = [
        key
        for key in ("SMTP_HOST", "SMTP_PORT", "SMTP_FROM")
        if not app.config.get(key)
    ]
    if missing:
        blocker = is_production(app)
        return {
            "status": "WARNING" if blocker else "DEGRADED",
            "blocker": blocker,
            "missing": missing,
            "ok": not blocker,
        }

    return {"status": "OK", "host": host, "blocker": False, "ok": True}


def check_notification_provider_readiness(app):
    try:
        from app.models.notification_center import NCNotificationProvider

        count = NCNotificationProvider.query.count()
        smtp = check_smtp_readiness(app)
        return {
            "status": "OK" if smtp.get("ok") or not is_production(app) else "WARNING",
            "providers": count,
            "smtp": smtp,
            "ok": smtp.get("ok") or not is_production(app),
        }
    except Exception as exc:
        smtp = check_smtp_readiness(app)
        return {
            "status": "DEGRADED",
            "error": str(exc),
            "smtp": smtp,
            "ok": smtp.get("ok") or not is_production(app),
        }


def validate_smtp(app):
    status = check_smtp_readiness(app)
    if is_production(app) and status.get("blocker"):
        raise RuntimeError("SMTP_HOST, SMTP_PORT, and SMTP_FROM are required in production")
    return True


def validate_production_config(app):
    if is_strict_env(app) and not app.config.get("TESTING"):
        validate_cors(app)
        validate_database(app)
        validate_redis(app)
        validate_smtp(app)
    return True


def evaluate_go_live_blockers(app):
    blockers = []
    warnings = []

    cors = cors_status(app)
    if not cors["ok"]:
        blockers.append(
            {
                "id": "cors_wildcard",
                "severity": "high",
                "message": "CORS_ORIGINS must be explicit in staging/production",
            }
        )

    database = database_dialect_report(app)
    if not database["ok"]:
        blockers.append(
            {
                "id": "sqlite_database",
                "severity": "high",
                "message": "SQLite DATABASE_URL is blocked in staging/production",
            }
        )
    elif database["postgresql_expected"] and database["dialect"] not in {"postgresql", "postgres"}:
        blockers.append(
            {
                "id": "postgresql_required",
                "severity": "high",
                "message": "PostgreSQL DATABASE_URL required for staging/production",
            }
        )

    redis = check_redis_health(app)
    if is_production(app) and not redis.get("ok"):
        blockers.append(
            {
                "id": "redis_unavailable",
                "severity": "high",
                "message": "Redis is required and must be reachable in production",
                "detail": redis,
            }
        )
    elif not redis.get("ok"):
        warnings.append(
            {
                "id": "redis_optional",
                "severity": "medium",
                "message": "Redis not configured; running in degraded mode",
                "detail": redis,
            }
        )

    smtp = check_smtp_readiness(app)
    if is_production(app) and not smtp.get("ok"):
        blockers.append(
            {
                "id": "smtp_not_configured",
                "severity": "high",
                "message": "SMTP must be configured in production",
                "detail": smtp,
            }
        )
    elif not smtp.get("ok"):
        warnings.append(
            {
                "id": "smtp_optional",
                "severity": "medium",
                "message": "SMTP not configured; notifications run in demo mode",
                "detail": smtp,
            }
        )

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "app_env": app_env(app),
        "ready": len(blockers) == 0,
        "blocker_count": len(blockers),
        "warning_count": len(warnings),
        "blockers": blockers,
        "warnings": warnings,
        "cors": cors,
        "database": database,
        "redis": redis,
        "smtp": smtp,
    }
