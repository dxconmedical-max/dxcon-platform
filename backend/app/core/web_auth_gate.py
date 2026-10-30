"""Authentication gate for server-rendered pages (everything outside /api/).

/api/ has its own gate (api_auth_gate). Server-rendered pages had none, so anonymous visitors could
open pages listing patients, orders, results and audit logs. Only the allow-list below (plus
WEB_AUTH_GATE_PUBLIC_PATHS) is reachable without login.
"""

from __future__ import annotations

import os

from flask import redirect, request

from app.core.authenticated_identity import (
    AuthenticatedIdentity,
    bind_authenticated_identity,
    get_authenticated_identity,
)
from app.core.errors import build_error_response

PUBLIC_EXACT = frozenset({"/health", "/live", "/ready", "/login", "/logout", "/favicon.ico", "/robots.txt"})
PUBLIC_PREFIXES = ("/static/", "/api/")


def gate_enabled() -> bool:
    return os.getenv("WEB_AUTH_GATE_ENABLED", "true").strip().lower() not in {"0", "false", "no", "off"}


def _extra_public() -> list[str]:
    raw = os.getenv("WEB_AUTH_GATE_PUBLIC_PATHS", "")
    return [p.strip() for p in raw.split(",") if p.strip().startswith("/")]


def is_public_path(path: str) -> bool:
    if path in PUBLIC_EXACT or path.startswith(PUBLIC_PREFIXES):
        return True
    for extra in _extra_public():
        if extra.endswith("/"):
            if path.startswith(extra):
                return True
        elif path == extra:
            return True
    return False


def _is_authenticated() -> bool:
    if isinstance(get_authenticated_identity(), AuthenticatedIdentity):
        return True
    try:
        result = bind_authenticated_identity()
    except Exception:
        return False
    return isinstance(result, AuthenticatedIdentity)


def init_web_auth_gate(app):
    @app.before_request
    def enforce_web_auth_gate():
        if app.config.get("TESTING") and not app.config.get("WEB_AUTH_GATE_IN_TESTS"):
            return None
        if not gate_enabled():
            return None
        if request.method == "OPTIONS":
            return None
        if is_public_path(request.path or ""):
            return None
        if _is_authenticated():
            return None
        if request.method in {"GET", "HEAD"}:
            return redirect("/login", code=302)
        return build_error_response("UNAUTHORIZED", "Authorization required", 401)
