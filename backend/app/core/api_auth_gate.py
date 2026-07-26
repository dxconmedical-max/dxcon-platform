"""Production API auth gate — deny anonymous access to high-risk prefixes.

Does not modify frozen web auth. Enforced in strict environments (staging/production)
unless TESTING is set. Accepts JWT Bearer or Flask session user_id (dual-auth workspaces).
"""

from __future__ import annotations

from flask import request, session
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request

from app.core.errors import build_error_response
from app.infrastructure.production_readiness import is_strict_env

# Exact public paths (auth not required).
PUBLIC_EXACT = frozenset(
    {
        "/api/v1/auth/login",
        "/api/v1/auth/register",
        "/api/v1/auth/refresh",
        "/api/v1/system/health",
        "/api/v1/system/live",
        "/api/v1/system/liveness",
        "/api/v1/system/ready",
        "/api/v1/system/readiness",
        "/api/v1/system/version",
        "/api/v1/system/build",
        "/api/v1/api-platform/health",
        "/live",
        "/ready",
    }
)

# Prefixes that remain public (verification QR, etc.).
PUBLIC_PREFIXES = (
    "/api/v1/reporting/verify/",
    "/results/verify/",
)

# High-risk API prefixes that must not be anonymous in strict env.
PROTECTED_PREFIXES = (
    "/api/v1/files",
    "/api/v1/seeds",
    "/api/v1/pilot-toolkit",
    "/api/v1/security",
    "/api/v1/security-compliance",
    "/api/v1/patients",
    "/api/v1/orders",
    "/api/v1/billing",
    "/api/v1/results",
    "/api/v1/partners",
    "/api/v1/collector",
    "/api/v1/shipments",
    "/api/v1/logistics-v2",
    "/api/v1/dashboard",
    "/api/v1/mobile",
    "/api/v1/admin",
    "/api/v1/system/routes",
    "/api/v1/system/stats",
    "/api/v1/system/diagnostics",
)


def _is_public(path: str) -> bool:
    if path in PUBLIC_EXACT:
        return True
    for prefix in PUBLIC_PREFIXES:
        if path.startswith(prefix):
            return True
    return False


def _is_protected(path: str) -> bool:
    for prefix in PROTECTED_PREFIXES:
        if path == prefix or path.startswith(prefix + "/") or path.startswith(prefix + "?"):
            return True
        # prefix without trailing segment match for exact blueprint roots
        if path.startswith(prefix):
            return True
    return False


def _authenticated() -> bool:
    if session.get("user_id"):
        return True
    try:
        verify_jwt_in_request(optional=True)
    except Exception:
        return False
    return bool(get_jwt_identity())


def init_api_auth_gate(app):
    @app.before_request
    def enforce_api_auth_gate():
        if app.config.get("TESTING"):
            return None
        if not app.config.get("API_AUTH_GATE_ENABLED", True):
            return None
        if not is_strict_env(app):
            return None

        if request.method == "OPTIONS":
            return None

        path = request.path or ""
        if not path.startswith("/api/"):
            return None
        if _is_public(path):
            return None
        if not _is_protected(path):
            return None
        if _authenticated():
            return None

        return build_error_response(
            "UNAUTHORIZED",
            "Authorization required",
            401,
        )
