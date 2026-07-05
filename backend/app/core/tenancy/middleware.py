"""Tenant middleware — optional resolution, backward compatible — Phase 7.1."""

from __future__ import annotations

from flask import g, request

from app.core.tenancy.resolver import TenantResolver


def init_tenant_middleware(app):
    """Attach TenantContext when tenant headers are present; never block legacy routes."""

    tenant_header = app.config.get("TENANT_ID_HEADER", "X-Tenant-ID")
    org_header = app.config.get("ORGANIZATION_ID_HEADER", "X-Organization-ID")

    @app.before_request
    def resolve_tenant_context():
        tenant_key = request.headers.get(tenant_header) or getattr(g, "tenant_id", None)
        org_key = request.headers.get(org_header)
        if not tenant_key:
            g.tenant_context = TenantResolver.resolve(None)
            return None

        ctx = TenantResolver.resolve(tenant_key, organization_id=org_key)
        g.tenant_context = ctx
        if ctx.resolved and ctx.tenant_id:
            g.tenant_id = ctx.tenant_id
        return None
