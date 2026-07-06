"""Executive platform API auth."""

from __future__ import annotations

from functools import wraps

from flask import session

from app.core.authz import roles_required
from app.executive_platform.security import (
    AUDIT_READ_ROLES,
    CRM_READ_ROLES,
    EXECUTIVE_READ_ROLES,
    EXECUTIVE_WRITE_ROLES,
    FINANCE_READ_ROLES,
    MONITORING_READ_ROLES,
    PILOT_READ_ROLES,
)


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


def executive_api_read(fn):
    return _dual(EXECUTIVE_READ_ROLES, fn)


def executive_api_write(fn):
    return _dual(EXECUTIVE_WRITE_ROLES, fn)


def crm_api_read(fn):
    return _dual(CRM_READ_ROLES, fn)


def finance_api_read(fn):
    return _dual(FINANCE_READ_ROLES, fn)


def monitoring_api_read(fn):
    return _dual(MONITORING_READ_ROLES, fn)


def audit_api_read(fn):
    return _dual(AUDIT_READ_ROLES, fn)


def pilot_api_read(fn):
    return _dual(PILOT_READ_ROLES, fn)
