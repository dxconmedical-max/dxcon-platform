"""Session or JWT auth for role dashboards."""

from __future__ import annotations

from functools import wraps

from flask import session

from app.core.authz import roles_required
from app.role_dashboards.security import ROLE_DASHBOARD_ROLES


def _session_role_ok(roles: frozenset) -> bool:
    return (session.get("role") or "") in roles and bool(session.get("user_id"))


def role_dashboard_auth(role_key: str):
    """Decorator factory: caller must hold a role allowed for the dashboard key."""

    allowed = ROLE_DASHBOARD_ROLES.get(role_key.lower(), frozenset())

    def decorator(fn):
        jwt_wrapped = roles_required(*allowed)(fn) if allowed else fn

        @wraps(fn)
        def wrapper(*args, **kwargs):
            if allowed and _session_role_ok(allowed):
                return fn(*args, **kwargs)
            if not allowed:
                return {"success": False, "error": f"Unknown dashboard role: {role_key}"}, 404
            return jwt_wrapped(*args, **kwargs)

        return wrapper

    return decorator
