from functools import wraps

from flask_jwt_extended import get_jwt, verify_jwt_in_request

from app.core.errors import build_error_response
from app.core.jwt_auth import require_active_user
from app.core.permissions import role_has_permission


def roles_required(*allowed_roles):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            active = require_active_user()
            if not isinstance(active, tuple):
                return active

            user, claims = active
            role = claims.get("role") or user.role

            if role not in allowed_roles:
                return build_error_response(
                    "FORBIDDEN",
                    "Insufficient role permissions",
                    403,
                )

            return fn(*args, **kwargs)

        return wrapper

    return decorator


def permission_required(permission):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            active = require_active_user()
            if not isinstance(active, tuple):
                return active

            user, claims = active
            role = claims.get("role") or user.role

            if not role_has_permission(role, permission):
                return build_error_response(
                    "FORBIDDEN",
                    f"Missing permission: {permission}",
                    403,
                )

            return fn(*args, **kwargs)

        return wrapper

    return decorator


def jwt_claims():
    verify_jwt_in_request()
    return get_jwt()
