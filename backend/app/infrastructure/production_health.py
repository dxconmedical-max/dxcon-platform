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


def _queue_ready(app, *, redis_required: bool) -> tuple[bool, str, dict]:
    from app.infrastructure.queue_provider import PRODUCTION_QUEUE_PROVIDER, get_queue, provider_name

    queue_name = provider_name(app)
    detail = {"provider": queue_name, "durable": False, "ping": False}
    if not redis_required:
        detail["ok"] = True
        return True, queue_name, detail
    if queue_name != PRODUCTION_QUEUE_PROVIDER:
        detail["ok"] = False
        detail["error"] = "QUEUE_PROVIDER must be redis in production"
        return False, queue_name, detail
    try:
        queue = get_queue(app)
        detail["durable"] = bool(getattr(queue, "durable", False))
        detail["ping"] = bool(queue.ping())
        detail["ok"] = detail["durable"] and detail["ping"]
        return detail["ok"], queue_name, detail
    except Exception as exc:
        detail["ok"] = False
        detail["error"] = str(exc)
        return False, queue_name, detail


def ready_payload(app) -> tuple[dict, int]:
    payload = _base_payload(app)
    db_ok = payload["database"] == "OK"
    redis_ok = payload["redis"] == "OK"
    redis_required = is_production(app)

    queue_ok, queue_name, queue_detail = _queue_ready(app, redis_required=redis_required)
    payload["queue_provider"] = queue_name
    payload["queue"] = queue_detail

    try:
        migrations_ready = bool(verify_migrations(app).get("ready", True))
    except Exception:
        migrations_ready = False

    ready = db_ok and migrations_ready and queue_ok and (redis_ok or not redis_required)
    payload["ready"] = ready
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
