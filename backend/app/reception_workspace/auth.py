"""Reception workspace API auth — session or JWT."""

from __future__ import annotations

from functools import wraps

from flask import session

from app.core.authz import roles_required
from app.reception_workspace.security import RECEPTION_READ_ROLES, RECEPTION_WRITE_ROLES


def _session_role_ok(roles: frozenset) -> bool:
    return (session.get("role") or "") in roles and bool(session.get("user_id"))


def reception_api_read(fn):
    jwt_wrapped = roles_required(*RECEPTION_READ_ROLES)(fn)

    @wraps(fn)
    def wrapper(*args, **kwargs):
        if _session_role_ok(RECEPTION_READ_ROLES):
            return fn(*args, **kwargs)
        return jwt_wrapped(*args, **kwargs)

    return wrapper


def reception_api_write(fn):
    jwt_wrapped = roles_required(*RECEPTION_WRITE_ROLES)(fn)

    @wraps(fn)
    def wrapper(*args, **kwargs):
        if _session_role_ok(RECEPTION_WRITE_ROLES):
            return fn(*args, **kwargs)
        return jwt_wrapped(*args, **kwargs)

    return wrapper
