"""Server-trusted authenticated identity (P0-A).

Identity is derived ONLY from JWT access tokens or Flask session.
Client headers (X-User-Email, X-User-Id, X-Clinic-Id, X-Doctor-Id,
X-Organization-ID, X-User-Role, etc.) are NEVER used as identity.

This module reuses flask_jwt_extended + existing User / auth_context_service.
It does not create a second authentication system.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from functools import wraps
from typing import Any, Callable

from flask import g, session
from flask_jwt_extended import get_jwt, get_jwt_identity, verify_jwt_in_request

from app.core.errors import build_error_response
from app.core.permissions import get_role_permissions
from app.models.user import User


@dataclass(frozen=True)
class AuthenticatedIdentity:
    """Canonical authenticated principal for the current request."""

    user_id: str
    email: str
    platform_role: str
    auth_method: str  # "jwt" | "session"
    organization_id: str | None = None
    organization_role: str | None = None
    membership_id: str | None = None
    permissions: tuple[str, ...] = field(default_factory=tuple)

    @property
    def user(self) -> User | None:
        return User.query.get(self.user_id)


_G_KEY = "authenticated_identity"
_G_REQUEST_KEY = "authenticated_identity_request"


def _unauthorized(message: str = "Authorization required", code: str = "UNAUTHORIZED"):
    return build_error_response(code, message, 401)


def _forbidden(message: str = "User account is disabled", code: str = "FORBIDDEN"):
    return build_error_response(code, message, 403)


def _cached_identity_for_current_request() -> AuthenticatedIdentity | None:
    """Return identity cached for *this* request only.

    Flask ``g`` is app-context scoped. Tests (and some workers) keep an app
    context across requests, so we must not reuse identity from a prior request.
    """
    from flask import has_request_context, request

    if not has_request_context():
        return None
    existing = getattr(g, _G_KEY, None)
    if not isinstance(existing, AuthenticatedIdentity):
        return None
    try:
        current = request._get_current_object()
    except RuntimeError:
        return None
    if getattr(g, _G_REQUEST_KEY, None) is not current:
        return None
    return existing


def _store_identity(identity: AuthenticatedIdentity) -> AuthenticatedIdentity:
    from flask import has_request_context, request

    setattr(g, _G_KEY, identity)
    g.user_id = identity.user_id
    if has_request_context():
        try:
            setattr(g, _G_REQUEST_KEY, request._get_current_object())
        except RuntimeError:
            pass
    return identity


def _membership_context(user: User) -> dict[str, Any]:
    """Best-effort org context from server-side memberships (never client headers)."""
    try:
        from app.services.auth_context_service import list_user_memberships

        memberships = list_user_memberships(user)
    except Exception:
        memberships = []

    selected = None
    if user.organization_id:
        selected = next(
            (m for m in memberships if m.get("organization_id") == user.organization_id),
            None,
        )
    if selected is None and memberships:
        selected = next(
            (m for m in memberships if m.get("membership_status") == "active"),
            memberships[0],
        )

    if not selected:
        return {
            "organization_id": user.organization_id,
            "organization_role": None,
            "membership_id": None,
        }
    return {
        "organization_id": selected.get("organization_id"),
        "organization_role": selected.get("role_code"),
        "membership_id": selected.get("membership_id"),
    }


def _merged_permissions(platform_role: str, organization_role: str | None) -> tuple[str, ...]:
    """Platform permissions ∪ active organization-role permissions (server-side only)."""
    platform = set(get_role_permissions(platform_role) or [])
    try:
        from app.partner_foundation.rbac import default_permissions_for_role

        org_perms = set(default_permissions_for_role(organization_role or "") or [])
    except Exception:
        org_perms = set()
    # SUPER_ADMIN platform role already expands via get_role_permissions; keep "*".
    from app.core.permissions import role_has_permission

    if role_has_permission(platform_role, "*"):
        return tuple(sorted(platform | org_perms | {"*"}))
    return tuple(sorted(platform | org_perms))


def _identity_from_user(user: User, *, auth_method: str, role_claim: str | None = None) -> AuthenticatedIdentity:
    # Platform role is always the persisted User.role. JWT/session claims are never
    # authoritative for elevation (role_claim retained only for mismatch detection).
    platform_role = (user.role or "").strip()
    if role_claim and role_claim != platform_role:
        # Stale/spoofed claim — ignore; DB wins.
        pass
    org = _membership_context(user)
    org_role = org.get("organization_role")
    perms = _merged_permissions(platform_role, org_role)
    return AuthenticatedIdentity(
        user_id=str(user.id),
        email=str(user.email or ""),
        platform_role=str(platform_role),
        auth_method=auth_method,
        organization_id=org.get("organization_id"),
        organization_role=org_role,
        membership_id=org.get("membership_id"),
        permissions=perms,
    )


def _resolve_from_session() -> AuthenticatedIdentity | None:
    user_id = session.get("user_id")
    if not user_id:
        return None
    user = User.query.get(user_id)
    if not user:
        return None
    if not user.is_active:
        return None
    # Platform role from session only if it matches the persisted user role.
    # Never accept X-User-Role. Session role is server-set at login.
    session_role = session.get("role")
    role_claim = session_role if session_role == user.role else user.role
    return _identity_from_user(user, auth_method="session", role_claim=role_claim)


def _resolve_from_jwt() -> AuthenticatedIdentity | tuple | None:
    """Return identity, error response tuple, or None if no JWT present."""
    try:
        verify_jwt_in_request(optional=True)
    except Exception:
        return _unauthorized("Invalid token", "INVALID_TOKEN")

    user_id = get_jwt_identity()
    if not user_id:
        return None

    try:
        claims = get_jwt() or {}
    except Exception:
        claims = {}

    # Access tokens only for API identity (refresh tokens are not API credentials).
    if claims.get("type") == "refresh":
        return _unauthorized("Access token required", "UNAUTHORIZED")

    user = User.query.get(user_id)
    if not user:
        return _unauthorized("User not found", "UNAUTHORIZED")
    if not user.is_active:
        return _forbidden()

    # Role from JWT claim only when it matches DB (prevents stale privilege).
    claim_role = claims.get("role")
    role_claim = claim_role if claim_role == user.role else user.role
    return _identity_from_user(user, auth_method="jwt", role_claim=role_claim)


def bind_authenticated_identity() -> AuthenticatedIdentity | tuple:
    """Resolve and bind identity to flask.g. Returns identity or error response."""
    existing = _cached_identity_for_current_request()
    if existing is not None:
        return existing

    # Prefer JWT when present; otherwise Flask session. Never client headers.
    jwt_result = _resolve_from_jwt()
    if isinstance(jwt_result, tuple):
        return jwt_result
    if isinstance(jwt_result, AuthenticatedIdentity):
        return _store_identity(jwt_result)

    session_identity = _resolve_from_session()
    if session_identity:
        return _store_identity(session_identity)

    return _unauthorized()


def get_authenticated_identity() -> AuthenticatedIdentity | None:
    identity = getattr(g, _G_KEY, None)
    return identity if isinstance(identity, AuthenticatedIdentity) else None


def get_authenticated_user() -> User | None:
    identity = get_authenticated_identity()
    if not identity:
        return None
    return User.query.get(identity.user_id)


def authenticated_actor_email() -> str:
    """Audit/actor email from authenticated identity only."""
    identity = get_authenticated_identity()
    if identity and identity.email:
        return identity.email
    user = get_authenticated_user()
    if user and user.email:
        return user.email
    raise RuntimeError("authenticated_actor_email called without authenticated identity")


def require_authenticated_user(fn: Callable | None = None):
    """Decorator: require JWT or session auth; bind AuthenticatedIdentity on g."""

    def decorator(view: Callable):
        @wraps(view)
        def wrapper(*args, **kwargs):
            result = bind_authenticated_identity()
            if not isinstance(result, AuthenticatedIdentity):
                return result
            return view(*args, **kwargs)

        return wrapper

    if fn is not None:
        return decorator(fn)
    return decorator


def blueprint_require_authenticated_user(blueprint) -> None:
    """Attach before_request auth gate to an entire blueprint."""

    @blueprint.before_request
    def _p0a_require_authenticated_user():
        result = bind_authenticated_identity()
        if not isinstance(result, AuthenticatedIdentity):
            return result
        return None


def blueprint_require_authenticated_user_except(
    blueprint,
    *,
    public_exact: frozenset[str] | set[str] | tuple[str, ...] = (),
    public_prefixes: tuple[str, ...] = (),
) -> None:
    """P0-A gate with intentional public-path exceptions (webhooks, catalogs).

    Does not create a second identity system. Skipped paths must still not
    treat client headers as identity; callers remain responsible for any
    non-human auth (device / webhook signature / service credential).
    """

    exact = frozenset(public_exact)
    prefixes = tuple(public_prefixes)

    @blueprint.before_request
    def _p0a_require_authenticated_user_except():
        from flask import request

        path = request.path or ""
        if path in exact:
            return None
        for prefix in prefixes:
            if path == prefix or path.startswith(prefix):
                return None
        result = bind_authenticated_identity()
        if not isinstance(result, AuthenticatedIdentity):
            return result
        return None
