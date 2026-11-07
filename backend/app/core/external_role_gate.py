"""Default-deny gate for external (tenant) roles such as clinic users.

Accounts whose platform role is in EXTERNAL_ROLES may only call a short allow-list; everything else returns 403,
even if an older page or API forgot to check roles. Staff roles and anonymous visitors are not affected here.
Kill switch: EXTERNAL_ROLE_GATE_ENABLED=false. Extra paths: EXTERNAL_GATE_EXTRA_PATHS (comma separated; trailing / = subtree).
"""

from __future__ import annotations

import os

from flask import request

from app.core.authenticated_identity import AuthenticatedIdentity, bind_authenticated_identity
from app.core.errors import build_error_response

CLINIC_VIEWER = "CLINIC_VIEWER"
EXTERNAL_ROLES = frozenset({CLINIC_VIEWER})

ALLOWED_EXACT = frozenset(
    {"/login", "/logout", "/health", "/live", "/ready",
     "/api/v1/system/health", "/api/v1/system/live", "/api/v1/system/ready"}
)
ALLOWED_PREFIXES = ("/static/", "/api/v1/auth/", "/api/v1/clinic-results/")

DENY_MESSAGE = "This account can only use the clinic results lookup"


def gate_enabled() -> bool:
    return os.getenv("EXTERNAL_ROLE_GATE_ENABLED", "true").strip().lower() not in {"0", "false", "no", "off"}


def _extra() -> list[str]:
    raw = os.getenv("EXTERNAL_GATE_EXTRA_PATHS", "")
    return [p.strip() for p in raw.split(",") if p.strip().startswith("/")]


def is_allowed_path(path: str) -> bool:
    if path in ALLOWED_EXACT or path.startswith(ALLOWED_PREFIXES):
        return True
    for extra in _extra():
        if extra.endswith("/"):
            if path.startswith(extra):
                return True
        elif path == extra:
            return True
    return False


def _identity():
    try:
        result = bind_authenticated_identity()
    except Exception:
        return None
    return result if isinstance(result, AuthenticatedIdentity) else None


def init_external_role_gate(app):
    @app.before_request
    def enforce_external_role_gate():
        if app.config.get("TESTING") and not app.config.get("EXTERNAL_ROLE_GATE_IN_TESTS"):
            return None
        if not gate_enabled() or request.method == "OPTIONS":
            return None
        if is_allowed_path(request.path or ""):
            return None
        identity = _identity()
        if identity is None or (identity.platform_role or "").upper() not in EXTERNAL_ROLES:
            return None
        return build_error_response("FORBIDDEN", DENY_MESSAGE, 403)
