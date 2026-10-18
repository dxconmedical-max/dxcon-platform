"""Organization scope and tenant isolation helpers.

P0-C: fail-closed by default. Prefer ``app.core.tenant_authorization`` for new code.
This module remains for partner_foundation callers and now delegates to membership-aware scope.
"""

from __future__ import annotations

from flask import session

from app.core.tenancy.context import get_tenant_context
from app.partner_foundation.rbac import GLOBAL_ORG_BYPASS_ROLES


def get_organization_scope(*, allow_global_bypass: bool = True) -> str | None:
    """Return membership-validated organization_id, or None only for platform global bypass.

    Legacy unscoped access for ordinary roles is removed (P0-C fail-closed).
    """
    try:
        from app.core.tenant_authorization import (
            AuthorizedTenant,
            get_authorized_tenant,
            resolve_authorized_tenant,
        )

        tenant = get_authorized_tenant()
        if tenant is None:
            # Best-effort resolve when identity is already bound; do not force auth here
            # for scripts that call get_organization_scope without a request user.
            from app.core.authenticated_identity import get_authenticated_identity

            if get_authenticated_identity() is not None:
                result = resolve_authorized_tenant(require_scope=False)
                if isinstance(result, AuthorizedTenant):
                    tenant = result
        if isinstance(tenant, AuthorizedTenant):
            if tenant.is_global_scope and allow_global_bypass:
                return None
            return tenant.organization_id
    except Exception:
        # Fall through to session/legacy scope resolution below.
        tenant = None

    role = (session.get("role") or "").upper() if session else None
    if allow_global_bypass and role in GLOBAL_ORG_BYPASS_ROLES:
        explicit = session.get("organization_id") if session else None
        if explicit:
            return explicit
        return None

    if session and session.get("organization_id"):
        return session.get("organization_id")

    ctx = get_tenant_context()
    if ctx and ctx.organization_id:
        return ctx.organization_id

    return None


def apply_organization_filter(query, model, *, column_name: str = "organization_id"):
    """Filter query by authorized organization. Fail-closed when scope is missing.

    SUPER_ADMIN global scope (None) passes through unfiltered intentionally.
    """
    try:
        from app.core.tenant_authorization import (
            AuthorizedTenant,
            apply_authorized_organization_filter,
            get_authorized_tenant,
            resolve_authorized_tenant,
        )

        tenant = get_authorized_tenant()
        if tenant is None:
            from app.core.authenticated_identity import get_authenticated_identity

            if get_authenticated_identity() is not None:
                result = resolve_authorized_tenant(require_scope=True)
                if isinstance(result, AuthorizedTenant):
                    tenant = result
                else:
                    # No valid scope → empty result set (fail-closed), not unfiltered query.
                    col = getattr(model, column_name, None)
                    if col is None:
                        return query.filter(False)
                    return query.filter(col.in_([]))
        if isinstance(tenant, AuthorizedTenant):
            if tenant.is_global_scope:
                return query
            return apply_authorized_organization_filter(query, model, column_name=column_name)
    except Exception:
        # Fall through to legacy org filter below (fail-closed when unscoped).
        query = query

    org_id = get_organization_scope()
    col = getattr(model, column_name, None)
    if col is None:
        return query.filter(False)
    if not org_id:
        # Fail-closed for non-global callers: never return all tenants.
        role = (session.get("role") or "").upper() if session else None
        if role in GLOBAL_ORG_BYPASS_ROLES:
            return query
        return query.filter(col.in_([]))
    return query.filter(col == org_id)


def assert_organization_access(
    record_org_id: str | None,
    user_org_id: str | None,
    *,
    role: str | None = None,
) -> bool:
    """Return True only when access is explicitly allowed (fail-closed)."""
    role_u = (role or "").upper()
    if role_u in GLOBAL_ORG_BYPASS_ROLES:
        return True
    if not user_org_id:
        return False
    if not record_org_id:
        return False
    return record_org_id == user_org_id
