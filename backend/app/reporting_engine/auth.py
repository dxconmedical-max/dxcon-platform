"""Reporting engine API auth."""

from __future__ import annotations

from functools import wraps

from flask import session

from app.core.authz import roles_required
from app.reporting_engine.security import (
    DOCTOR_APPROVE_ROLES,
    DOCTOR_RELEASE_ROLES,
    PATIENT_REPORT_ROLES,
    REPORT_READ_ROLES,
    REPORT_WRITE_ROLES,
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


def report_api_read(fn):
    return _dual(REPORT_READ_ROLES, fn)


def report_api_write(fn):
    return _dual(REPORT_WRITE_ROLES, fn)


def report_api_approve(fn):
    return _dual(DOCTOR_APPROVE_ROLES, fn)


def report_api_release(fn):
    return _dual(DOCTOR_RELEASE_ROLES, fn)


def patient_report_read(fn):
    return _dual(PATIENT_REPORT_ROLES, fn)
