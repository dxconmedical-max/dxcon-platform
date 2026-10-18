"""Canonical audit actor derivation (P0-5).

Human actors come from AuthenticatedIdentity (JWT / verified session).
Device actors come from AuthenticatedDevice (P0-D).
System actors are explicit server-controlled names.

Client headers (X-User-Email, X-Actor, X-User-Role, X-Driver-Id, X-Vehicle-Id,
X-Device-Id, X-Organization-ID, X-Partner-ID) are never used as audit identity.
"""

from __future__ import annotations

import re
from typing import Any

from app.core.authenticated_identity import (
    AuthenticatedIdentity,
    bind_authenticated_identity,
    get_authenticated_identity,
)
from app.core.logging_config import redact_mapping

_SAFE_SYSTEM_NAME = re.compile(r"^[A-Za-z0-9_.-]{1,80}$")

SYSTEM_ACTOR_PREFIX = "system:"
DEVICE_ACTOR_PREFIX = "device:"

_SECRET_HINTS = (
    "password",
    "password_hash",
    "bearer ",
    "x-device-secret",
    "device_secret",
    "api_key",
    "authorization",
    "refresh_token",
    "access_token",
)


def is_device_actor(value: str | None) -> bool:
    return bool(value) and str(value).startswith(DEVICE_ACTOR_PREFIX)


def is_system_actor(value: str | None) -> bool:
    if not value:
        return False
    text = str(value)
    return text.startswith(SYSTEM_ACTOR_PREFIX) or text == "SYSTEM"


def system_audit_actor(name: str) -> str:
    raw = (name or "job").strip()
    if not _SAFE_SYSTEM_NAME.match(raw):
        raw = "job"
    return f"{SYSTEM_ACTOR_PREFIX}{raw}"


def device_audit_actor(auth_device) -> str:
    actor = getattr(auth_device, "device_actor", None)
    if actor:
        return str(actor)
    device = getattr(auth_device, "device", None)
    code = getattr(device, "device_code", None) or getattr(device, "id", "unknown")
    return f"{DEVICE_ACTOR_PREFIX}{code}"


def _try_bind_identity() -> AuthenticatedIdentity | None:
    existing = get_authenticated_identity()
    if isinstance(existing, AuthenticatedIdentity):
        return existing
    try:
        result = bind_authenticated_identity()
    except Exception:
        return None
    if isinstance(result, AuthenticatedIdentity):
        return result
    return None


def resolve_human_audit_actor(*, unauthenticated_fallback: str | None = "SYSTEM") -> str | None:
    """Return authenticated human email, else a server-controlled fallback.

    Never reads X-User-Email / X-Actor / body actor fields.
    """
    identity = _try_bind_identity()
    if identity and identity.email:
        return identity.email
    if unauthenticated_fallback is None:
        return None
    if unauthenticated_fallback == "" or is_system_actor(unauthenticated_fallback):
        return unauthenticated_fallback or None
    return "SYSTEM"


def require_human_audit_actor():
    """Return ``(email, None)`` or ``(None, error_response_tuple)``."""
    identity = _try_bind_identity()
    if identity and identity.email:
        return identity.email, None
    from app.core.errors import build_error_response

    return None, build_error_response("UNAUTHORIZED", "Authorization required", 401)


def canonicalize_audit_actor(user_email: str | None) -> str:
    """Defense in depth for durable audit writes.

    - ``device:`` / ``system:`` prefixes are preserved (server-derived callers).
    - If a human identity is bound, it always wins over a client-supplied email.
    - Inside an HTTP request, unauthenticated client strings are not trusted.
    - Outside a request (jobs/scripts), an explicit server-passed actor is kept.
    """
    value = (user_email or "").strip()
    if contains_secret_material(value):
        value = ""
    if is_device_actor(value) or value.startswith(SYSTEM_ACTOR_PREFIX):
        return value

    identity = get_authenticated_identity()
    if identity and identity.email:
        return identity.email

    try:
        from flask import has_request_context

        in_request = has_request_context()
    except Exception:
        in_request = False

    if in_request:
        return "SYSTEM"
    return value or "SYSTEM"


def contains_secret_material(text: str | None) -> bool:
    if not text:
        return False
    lowered = str(text).lower()
    return any(hint in lowered for hint in _SECRET_HINTS)


def sanitize_audit_payload(payload: Any) -> Any:
    if isinstance(payload, dict):
        return redact_mapping(payload)
    return payload
