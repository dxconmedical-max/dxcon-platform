"""Patient portal API auth."""

from __future__ import annotations

from functools import wraps

from flask import session

from app.core.authz import roles_required
from app.patient_portal.security import PATIENT_PORTAL_READ_ROLES, PATIENT_PORTAL_WRITE_ROLES


def _session_role_ok(roles: frozenset) -> bool:
    return (session.get("role") or "") in roles and bool(session.get("user_id"))


def _dual(roles, fn):
    jwt_wrapped = roles_required(*roles)(fn)

    @wraps(fn)
    def wrapper(*args, **kwargs):
        if _session_role_ok(roles):
            return fn(*args, **kwargs)
        return jwt_wrapped(*args, **kwargs)

    return wrapper


def patient_portal_read(fn):
    return _dual(PATIENT_PORTAL_READ_ROLES, fn)


def patient_portal_write(fn):
    return _dual(PATIENT_PORTAL_WRITE_ROLES, fn)
