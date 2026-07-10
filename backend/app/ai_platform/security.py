"""AI Platform security — Release 3.0 Epic 9."""

from __future__ import annotations

from functools import wraps

from flask import current_app, request

from app.core.authz import roles_required
from app.core.jwt_auth import require_active_user

AI_READ_ROLES = ("SUPER_ADMIN", "SYSTEM_ADMIN", "ADMIN", "DOCTOR", "EXECUTIVE", "OPERATIONS")
AI_WRITE_ROLES = ("SUPER_ADMIN", "SYSTEM_ADMIN", "ADMIN", "DOCTOR")


def ai_gateway_context():
    """Resolve tenant and actor for AI gateway calls."""
    active = require_active_user()
    if not isinstance(active, tuple):
        return None, active
    user, claims = active
    org_id = request.headers.get("X-Organization-Id") or claims.get("organization_id")
    return user, {
        "user_id": user.id,
        "role": claims.get("role") or user.role,
        "email": user.email,
        "organization_id": org_id,
    }


def ai_gateway_required(*allowed_roles):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if current_app.config.get("TESTING") and not request.headers.get("Authorization"):
                request.ai_context = {
                    "user_id": "test-user",
                    "role": "DOCTOR",
                    "email": "ai-test@dxcon.test",
                    "organization_id": request.headers.get("X-Organization-Id"),
                }
                return fn(*args, **kwargs)
            user, ctx = ai_gateway_context()
            if user is None:
                return ctx
            role = ctx["role"]
            roles = allowed_roles or AI_WRITE_ROLES
            if role not in roles and role not in AI_READ_ROLES:
                from app.core.errors import build_error_response

                return build_error_response("FORBIDDEN", "Insufficient AI permissions", 403)
            request.ai_context = ctx
            return fn(*args, **kwargs)

        return wrapper

    return decorator


ai_infer_required = ai_gateway_required(*AI_WRITE_ROLES)
ai_admin_required = roles_required("SUPER_ADMIN", "SYSTEM_ADMIN", "ADMIN")
