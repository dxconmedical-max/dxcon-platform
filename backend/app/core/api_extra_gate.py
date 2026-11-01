"""Extra authentication gate for API groups that were reachable anonymously.

Health/live/ready stay public. Kill switch: API_EXTRA_GATE_ENABLED=false.
Extra public paths: API_EXTRA_GATE_PUBLIC_PATHS (comma separated; a trailing / means a whole subtree).
"""

from __future__ import annotations

import os

from flask import request, session
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request

from app.core.errors import build_error_response

PROTECTED_PREFIXES = (
    "/api/v1/ai-copilot",
    "/api/v1/ai-operations",
    "/api/v1/ai-v2",
    "/api/v1/api-platform",
    "/api/v1/backup-recovery",
    "/api/v1/data-warehouse",
    "/api/v1/developer-portal",
)
PROTECTED_EXACT = frozenset(
    {"/api/v1/system/build", "/api/v1/system/metrics", "/api/v1/system/version"}
)


def gate_enabled() -> bool:
    return os.getenv("API_EXTRA_GATE_ENABLED", "true").strip().lower() not in {"0", "false", "no", "off"}


def _extra_public() -> list[str]:
    raw = os.getenv("API_EXTRA_GATE_PUBLIC_PATHS", "")
    return [p.strip() for p in raw.split(",") if p.strip().startswith("/")]


def is_protected(path: str) -> bool:
    for extra in _extra_public():
        if extra.endswith("/"):
            if path.startswith(extra):
                return False
        elif path == extra:
            return False
    if path in PROTECTED_EXACT:
        return True
    return any(path == p or path.startswith(p + "/") for p in PROTECTED_PREFIXES)


def _authenticated() -> bool:
    if session.get("user_id"):
        return True
    try:
        verify_jwt_in_request(optional=True)
    except Exception:
        return False
    return bool(get_jwt_identity())


def init_api_extra_gate(app):
    @app.before_request
    def enforce_api_extra_gate():
        if app.config.get("TESTING") and not app.config.get("API_EXTRA_GATE_IN_TESTS"):
            return None
        if not gate_enabled() or request.method == "OPTIONS":
            return None
        if not is_protected(request.path or ""):
            return None
        if _authenticated():
            return None
        return build_error_response("UNAUTHORIZED", "Authorization required", 401)
