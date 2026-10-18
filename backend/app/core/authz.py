"""Canonical server-side authorization (P0-B).

Builds on AuthenticatedIdentity (P0-A). Authorization answers:

1. Is the user authenticated?
2. What platform role does the user have? (User.role in DB)
3. What organization memberships does the user have?
4. What organization role in the active organization?
5. Does that role have permission for this action?

Client-supplied role / permission / capability / is_admin / admin values in
headers, query parameters, or request body are NEVER trusted for authorization.
"""

from __future__ import annotations

from functools import wraps

from flask_jwt_extended import get_jwt, verify_jwt_in_request

from app.core.authenticated_identity import (
    AuthenticatedIdentity,
    bind_authenticated_identity,
    get_authenticated_identity,
)
from app.core.errors import build_error_response
from app.core.permissions import role_has_permission
from app.partner_foundation.rbac import GLOBAL_ORG_BYPASS_ROLES, org_role_has_permission


def _forbidden(message: str = "Insufficient role permissions", code: str = "FORBIDDEN"):
    return build_error_response(code, message, 403)


def identity_has_platform_role(identity: AuthenticatedIdentity, *allowed_roles: str) -> bool:
    return bool(identity.platform_role) and identity.platform_role in allowed_roles


def identity_has_org_role(identity: AuthenticatedIdentity, *allowed_org_roles: str) -> bool:
    if identity.platform_role in GLOBAL_ORG_BYPASS_ROLES:
        return True
    return bool(identity.organization_role) and identity.organization_role in allowed_org_roles


def identity_has_permission(identity: AuthenticatedIdentity, permission: str) -> bool:
    if role_has_permission(identity.platform_role, permission):
        return True
    if identity.organization_role and org_role_has_permission(
        identity.organization_role, permission
    ):
        return True
    return permission in (identity.permissions or ())


def _bind_or_error():
    result = bind_authenticated_identity()
    if not isinstance(result, AuthenticatedIdentity):
        return result
    return result


def roles_required(*allowed_roles):
    """Require authenticated identity with one of the given *platform* roles."""

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            result = _bind_or_error()
            if not isinstance(result, AuthenticatedIdentity):
                return result
            if not identity_has_platform_role(result, *allowed_roles):
                return _forbidden("Insufficient role permissions")
            return fn(*args, **kwargs)

        return wrapper

    return decorator


def require_platform_role(*allowed_roles):
    """Explicit platform-role gate (preferred name for new code)."""
    return roles_required(*allowed_roles)


def require_role(*allowed_roles):
    """Alias for platform role checks (project equivalent of require_role)."""
    return roles_required(*allowed_roles)


def permission_required(permission: str):
    """Require a permission via platform role and/or active org role."""

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            result = _bind_or_error()
            if not isinstance(result, AuthenticatedIdentity):
                return result
            if not identity_has_permission(result, permission):
                return _forbidden(f"Missing permission: {permission}")
            return fn(*args, **kwargs)

        return wrapper

    return decorator


def require_permission(permission: str):
    """Preferred alias for permission_required."""
    return permission_required(permission)


def require_org_role(*allowed_org_roles: str):
    """Require organization membership role (or platform org-bypass role)."""

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            result = _bind_or_error()
            if not isinstance(result, AuthenticatedIdentity):
                return result
            if not identity_has_org_role(result, *allowed_org_roles):
                return _forbidden("Insufficient organization role permissions")
            return fn(*args, **kwargs)

        return wrapper

    return decorator


def current_platform_role() -> str | None:
    """Server-derived platform role for the current request, if authenticated."""
    identity = get_authenticated_identity()
    if identity is None:
        result = bind_authenticated_identity()
        if not isinstance(result, AuthenticatedIdentity):
            return None
        identity = result
    return identity.platform_role


def jwt_claims():
    verify_jwt_in_request()
    return get_jwt()
