"""Device and staff authorization for IoT platform."""

from __future__ import annotations

import hashlib
import hmac
import os
from functools import wraps

from flask import request, session

from app.core.authz import roles_required
from app.extensions.db import db
from app.models.iot_platform import IoTDeviceCredential


IOT_STAFF_ROLES = frozenset({"SUPER_ADMIN", "ADMIN", "LAB", "COLLECTOR", "OPERATIONS"})
IOT_WRITE_ROLES = frozenset({"SUPER_ADMIN", "ADMIN", "LAB", "OPERATIONS"})


def _session_role_ok(roles: frozenset) -> bool:
    return (session.get("role") or "") in roles and bool(session.get("user_id"))


def iot_api_read(fn):
    jwt_wrapped = roles_required(*IOT_STAFF_ROLES)(fn)

    @wraps(fn)
    def wrapper(*args, **kwargs):
        if _session_role_ok(IOT_STAFF_ROLES):
            return fn(*args, **kwargs)
        return jwt_wrapped(*args, **kwargs)

    return wrapper


def iot_api_write(fn):
    jwt_wrapped = roles_required(*IOT_WRITE_ROLES)(fn)

    @wraps(fn)
    def wrapper(*args, **kwargs):
        if _session_role_ok(IOT_WRITE_ROLES):
            return fn(*args, **kwargs)
        return jwt_wrapped(*args, **kwargs)

    return wrapper


def hash_device_secret(secret: str) -> str:
    return hashlib.sha256(secret.encode("utf-8")).hexdigest()


def verify_device_token(device_id: str, token: str | None) -> bool:
    if not token:
        return False
    cred = (
        IoTDeviceCredential.query.filter_by(device_id=device_id)
        .order_by(IoTDeviceCredential.created_at.desc())
        .first()
    )
    if not cred:
        return False
    return hmac.compare_digest(cred.credential_hash, hash_device_secret(token))


def device_ingest_auth(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        device_id = request.headers.get("X-Device-ID") or (request.get_json(silent=True) or {}).get("device_id")
        token = request.headers.get("X-Device-Token")
        if not device_id or not verify_device_token(device_id, token):
            return {"error": "Unauthorized device"}, 401
        return fn(*args, **kwargs)

    return wrapper


def simulator_allowed() -> bool:
    env = os.environ.get("FLASK_ENV", os.environ.get("ENVIRONMENT", "development"))
    explicit = os.environ.get("IOT_SIMULATOR_ENABLED", "").lower()
    if env == "production":
        return explicit == "true" and os.environ.get("IOT_SIMULATOR_FORCE") == "true"
    return explicit != "false"
