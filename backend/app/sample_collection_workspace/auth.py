"""Sample Collection workspace API auth — session or JWT."""

from __future__ import annotations

from functools import wraps

from flask import session

from app.core.authz import roles_required
from app.sample_collection_workspace.security import (
    COLLECTION_READ_ROLES,
    COLLECTION_WRITE_ROLES,
)


def _session_role_ok(roles: frozenset) -> bool:
    return (session.get("role") or "") in roles and bool(session.get("user_id"))


def collection_api_read(fn):
    jwt_wrapped = roles_required(*COLLECTION_READ_ROLES)(fn)

    @wraps(fn)
    def wrapper(*args, **kwargs):
        if _session_role_ok(COLLECTION_READ_ROLES):
            return fn(*args, **kwargs)
        return jwt_wrapped(*args, **kwargs)

    return wrapper


def collection_api_write(fn):
    jwt_wrapped = roles_required(*COLLECTION_WRITE_ROLES)(fn)

    @wraps(fn)
    def wrapper(*args, **kwargs):
        if _session_role_ok(COLLECTION_WRITE_ROLES):
            return fn(*args, **kwargs)
        return jwt_wrapped(*args, **kwargs)

    return wrapper
