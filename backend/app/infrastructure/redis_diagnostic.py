"""Temporary SUPER_ADMIN Redis diagnostic — no secrets in responses or logs."""

from __future__ import annotations

import logging
import os
import socket
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger("dxcon.redis_diagnostic")

PING_CONNECT_TIMEOUT_SECONDS = 3
PING_SOCKET_TIMEOUT_SECONDS = 5


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def runtime_label() -> str:
    if os.environ.get("RENDER") or os.environ.get("RENDER_SERVICE_ID"):
        return "render"
    return "non_render"


def sanitize_error_type(exc: BaseException) -> str:
    """Return a stable exception class name only — never message/URL/host."""
    name = type(exc).__name__
    # Normalize common redis/socket wrappers without leaking details.
    module = type(exc).__module__ or ""
    if name in {"TimeoutError", "socket.timeout"} or "Timeout" in name:
        return "TimeoutError"
    if name in {"gaierror", "herror"}:
        return "NameResolutionError"
    if name in {"ConnectionError", "ConnectionRefusedError", "OSError"} and "redis" in module:
        # redis.exceptions.ConnectionError often wraps DNS; keep ConnectionError
        msg = str(exc).lower()
        if "name or service not known" in msg or "nodename nor servname" in msg or "errno -2" in msg or "error -2" in msg:
            return "NameResolutionError"
        if "timed out" in msg or "timeout" in msg:
            return "TimeoutError"
        return "ConnectionError"
    if name == "ConnectionRefusedError":
        return "ConnectionRefusedError"
    if name == "AuthenticationError" or "auth" in name.lower():
        return "AuthenticationError"
    if name == "ImportError":
        return "ImportError"
    # Strip accidental host/url fragments if class name is weird
    if "://" in name or "@" in name:
        return "Error"
    return name


def get_redis_client(app):
    """Build client from app config only (existing REDIS_URL pattern)."""
    import redis

    url = (app.config.get("REDIS_URL") or "").strip()
    if not url:
        raise RuntimeError("REDIS_URL_NOT_CONFIGURED")
    return redis.from_url(
        url,
        socket_connect_timeout=PING_CONNECT_TIMEOUT_SECONDS,
        socket_timeout=PING_SOCKET_TIMEOUT_SECONDS,
    )


def ping_redis_diagnostic(app) -> dict[str, Any]:
    """Execute Redis PING inside the current runtime. Never includes secrets."""
    checked_at = _utc_now()
    runtime = runtime_label()
    correlation_id = None
    try:
        from app.core.request_context import get_correlation_id, get_request_id

        correlation_id = get_correlation_id() or get_request_id()
    except Exception:
        correlation_id = None

    try:
        client = get_redis_client(app)
        result = client.ping()
        ok = bool(result)
        if not ok:
            payload = {
                "service": "redis",
                "status": "error",
                "ping": False,
                "error_type": "PingFailed",
                "checked_at": checked_at,
            }
            logger.info(
                "redis_diagnostic result=error error_type=PingFailed correlation_id=%s",
                correlation_id or "-",
            )
            return payload

        payload = {
            "service": "redis",
            "status": "ok",
            "ping": True,
            "runtime": runtime,
            "checked_at": checked_at,
        }
        logger.info(
            "redis_diagnostic result=ok correlation_id=%s",
            correlation_id or "-",
        )
        return payload
    except Exception as exc:  # noqa: BLE001 — diagnostic must never raise secrets outward
        if isinstance(exc, RuntimeError) and str(exc) == "REDIS_URL_NOT_CONFIGURED":
            error_type = "NotConfigured"
        elif isinstance(exc, socket.timeout):
            error_type = "TimeoutError"
        elif isinstance(exc, socket.gaierror):
            error_type = "NameResolutionError"
        else:
            error_type = sanitize_error_type(exc)

        logger.info(
            "redis_diagnostic result=error error_type=%s correlation_id=%s",
            error_type,
            correlation_id or "-",
        )
        return {
            "service": "redis",
            "status": "error",
            "ping": False,
            "error_type": error_type,
            "checked_at": checked_at,
        }
