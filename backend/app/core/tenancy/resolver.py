"""Resolve tenant identifiers to validated TenantContext — Phase 7.1."""

from __future__ import annotations

from app.core.tenancy.context import TenantContext
from app.models.enterprise_platform import EnterpriseOrganization, EnterpriseTenant


class TenantResolver:
    """Resolve tenant by UUID or tenant_code without breaking legacy requests."""

    @staticmethod
    def resolve(identifier: str | None, organization_id: str | None = None) -> TenantContext:
        if not identifier:
            return TenantContext(resolved=False, source="none")

        tenant = EnterpriseTenant.query.filter(
            (EnterpriseTenant.id == identifier) | (EnterpriseTenant.tenant_code == identifier)
        ).first()
        if not tenant:
            return TenantContext(tenant_id=identifier, resolved=False, source="header_unresolved")

        org = None
        if organization_id:
            org = EnterpriseOrganization.query.filter_by(id=organization_id, tenant_id=tenant.id).first()
        elif tenant:
            org = EnterpriseOrganization.query.filter_by(tenant_id=tenant.id).order_by(
                EnterpriseOrganization.level.asc()
            ).first()

        return TenantContext(
            tenant_id=tenant.id,
            tenant_code=tenant.tenant_code,
            tenant_name=tenant.name,
            organization_id=org.id if org else None,
            organization_code=org.org_code if org else None,
            isolation_mode=tenant.isolation_mode,
            schema_name=tenant.schema_name,
            resolved=True,
            source="resolver",
        )

    @staticmethod
    def describe() -> dict:
        return {
            "resolver": "TenantResolver",
            "inputs": ["X-Tenant-ID header (uuid or tenant_code)", "optional X-Organization-ID"],
            "behavior": "non_blocking",
            "legacy_compatible": True,
        }
