"""Organization scope and tenant isolation helpers."""

from __future__ import annotations

from flask import g, session

from app.core.tenancy.context import get_tenant_context


def get_organization_scope(*, allow_global_bypass: bool = True) -> str | None:
    """Return active organization_id for query filtering, or None for legacy unscoped access."""
    role = (session.get("role") or "").upper() if session else None
    if allow_global_bypass and role in {"SUPER_ADMIN", "SYSTEM_ADMIN"}:
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
    """Filter query by organization when scope is resolved; otherwise pass-through."""
    org_id = get_organization_scope()
    if not org_id:
        return query
    col = getattr(model, column_name, None)
    if col is None:
        return query
    return query.filter((col == org_id) | (col.is_(None)))


def assert_organization_access(record_org_id: str | None, user_org_id: str | None, *, role: str | None = None) -> bool:
    if (role or "").upper() in {"SUPER_ADMIN", "SYSTEM_ADMIN"}:
        return True
    if not user_org_id:
        return True
    if not record_org_id:
        return True
    return record_org_id == user_org_id
