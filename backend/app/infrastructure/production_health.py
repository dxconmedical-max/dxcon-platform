"""Production probe payloads for /health, /ready, and /live."""

from __future__ import annotations

from datetime import datetime, timezone

from app.core.database_startup import verify_database_connection, verify_migrations
from app.infrastructure.production_readiness import app_env, check_redis_health, is_production


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def _database_status(app) -> str:
    try:
        verify_database_connection(app, retries=1, delay_seconds=0)
        return "OK"
    except Exception:
        return "ERROR"


def _redis_status(app) -> str:
    return check_redis_health(app).get("status", "DEGRADED")


def _base_payload(app) -> dict:
    return {
        "app_env": app_env(app),
        "database": _database_status(app),
        "redis": _redis_status(app),
        "timestamp": _timestamp(),
    }


def live_payload(app) -> tuple[dict, int]:
    payload = _base_payload(app)
    payload["status"] = "OK"
    return payload, 200


def ready_payload(app) -> tuple[dict, int]:
    payload = _base_payload(app)
    db_ok = payload["database"] == "OK"
    redis_ok = payload["redis"] == "OK"
    redis_required = is_production(app)

    try:
        migrations_ready = bool(verify_migrations(app).get("ready", True))
    except Exception:
        migrations_ready = False

    ready = db_ok and migrations_ready and (redis_ok or not redis_required)
    if not db_ok:
        payload["status"] = "ERROR"
    elif ready:
        payload["status"] = "OK"
    else:
        payload["status"] = "DEGRADED"
    return payload, 200 if ready else 503


def health_payload(app) -> tuple[dict, int]:
    payload = _base_payload(app)
    db_ok = payload["database"] == "OK"
    redis_ok = payload["redis"] == "OK"
    redis_required = is_production(app)

    if not db_ok:
        payload["status"] = "DEGRADED"
    elif redis_required and payload["redis"] == "DOWN":
        payload["status"] = "ERROR"
    elif redis_required and not redis_ok:
        payload["status"] = "DEGRADED"
    else:
        payload["status"] = "OK"

    status_code = 503 if payload["status"] == "ERROR" else 200
    return payload, status_code
