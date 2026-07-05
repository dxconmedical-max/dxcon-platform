"""Lab workspace API auth — session or JWT."""

from __future__ import annotations

from functools import wraps

from flask import session

from app.core.authz import roles_required
from app.lab_workspace.security import LAB_ADMIN_ROLES, LAB_READ_ROLES, LAB_SUPERVISOR_ROLES, LAB_WRITE_ROLES


def _session_role_ok(roles: frozenset) -> bool:
    return (session.get("role") or "") in roles and bool(session.get("user_id"))


def _dual_auth(roles: frozenset, fn):
    jwt_wrapped = roles_required(*roles)(fn)

    @wraps(fn)
    def wrapper(*args, **kwargs):
        if _session_role_ok(roles):
            return fn(*args, **kwargs)
        return jwt_wrapped(*args, **kwargs)

    return wrapper


def lab_api_read(fn):
    return _dual_auth(LAB_READ_ROLES, fn)


def lab_api_write(fn):
    return _dual_auth(LAB_WRITE_ROLES, fn)


def lab_api_supervisor(fn):
    return _dual_auth(LAB_SUPERVISOR_ROLES, fn)


def lab_api_admin(fn):
    return _dual_auth(LAB_ADMIN_ROLES, fn)
