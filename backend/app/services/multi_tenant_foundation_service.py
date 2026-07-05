"""Multi-tenant foundation business logic for Phase 7.1."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from flask import current_app

from app.core.tenancy.context import TenantContext
from app.core.tenancy.resolver import TenantResolver
from app.extensions.db import db
from app.models.clinic_profile import ClinicProfile
from app.models.enterprise_platform import (
    EnterpriseOrganization,
    EnterpriseTenant,
    TenantOrganizationSetting,
)
from app.models.laboratory import Laboratory
from app.services.enterprise_platform_service import (
    AdminEnterpriseService,
    AuditEnterpriseService,
    OrganizationEnterpriseService,
    TenantEnterpriseService,
)
from app.services.reporting_service import _safe
from app.services.tenant_isolation_service import ensure_demo_clinics, tenant_isolation_matrix

MULTI_TENANT_ROLES = ("SUPER_ADMIN", "ADMIN")

FEATURES = (
    "Tenant",
    "Organization",
    "Clinic",
    "Laboratory",
    "Organization Settings",
    "Tenant Resolver",
    "Tenant Context",
    "Tenant Middleware",
    "Tenant Admin",
    "Tenant Audit",
    "Tenant Isolation Framework",
)


class MultiTenantFoundationError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


def ensure_multi_tenant_foundation() -> dict[str, Any]:
    _ensure_tenant_columns()
    ensure_demo_clinics()
    _link_operational_entities()
    _ensure_default_org_settings()
    return {"ready": True}


def _ensure_tenant_columns() -> None:
    """Add nullable tenant/org FK columns to existing tables when absent."""
    from sqlalchemy import inspect, text

    from app.infrastructure.schema_introspection import get_table_columns, table_exists_name

    specs = (
        ("clinic_profiles", "tenant_id", "VARCHAR(36)"),
        ("clinic_profiles", "organization_id", "VARCHAR(36)"),
        ("laboratories", "tenant_id", "VARCHAR(36)"),
        ("laboratories", "organization_id", "VARCHAR(36)"),
    )
    inspector = inspect(db.engine)
    for table, column, col_type in specs:
        if not table_exists_name(table):
            continue
        if column in get_table_columns(table):
            continue
        with db.engine.begin() as conn:
            conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}"))


def _link_operational_entities() -> dict[str, Any]:
    linked_clinics = 0
    linked_labs = 0
    tenants = EnterpriseTenant.query.all()
    for index, tenant in enumerate(tenants):
        org = EnterpriseOrganization.query.filter_by(tenant_id=tenant.id).first()
        clinic = ClinicProfile.query.filter(
            (ClinicProfile.tenant_id.is_(None)) | (ClinicProfile.tenant_id == tenant.id)
        ).offset(index).first()
        if clinic and not clinic.tenant_id:
            clinic.tenant_id = tenant.id
            if org:
                clinic.organization_id = org.id
            linked_clinics += 1
        lab = Laboratory.query.filter(
            (Laboratory.tenant_id.is_(None)) | (Laboratory.tenant_id == tenant.id)
        ).offset(index).first()
        if lab and not lab.tenant_id:
            lab.tenant_id = tenant.id
            if org:
                lab.organization_id = org.id
            linked_labs += 1
    if linked_clinics or linked_labs:
        db.session.commit()
    return {"linked_clinics": linked_clinics, "linked_labs": linked_labs}


def _ensure_default_org_settings() -> None:
    tenant = EnterpriseTenant.query.first()
    if not tenant:
        return
    defaults = (
        ("timezone", "Asia/Ho_Chi_Minh", "LOCALE"),
        ("locale", "vi-VN", "LOCALE"),
        ("data_retention_days", "2555", "COMPLIANCE"),
    )
    for key, value, category in defaults:
        exists = TenantOrganizationSetting.query.filter_by(tenant_id=tenant.id, setting_key=key).first()
        if exists:
            continue
        db.session.add(
            TenantOrganizationSetting(
                tenant_id=tenant.id,
                setting_key=key,
                setting_value=value,
                category=category,
            )
        )
    db.session.commit()


def tenant_registry() -> dict[str, Any]:
    ensure_multi_tenant_foundation()
    payload = TenantEnterpriseService.list_tenants()
    payload["report"] = "tenant_registry"
    payload["read_only"] = False
    return payload


def organization_registry(tenant_id: str | None = None) -> dict[str, Any]:
    ensure_multi_tenant_foundation()
    payload = OrganizationEnterpriseService.list_organizations(tenant_id)
    payload["report"] = "organization_registry"
    payload["read_only"] = False
    return payload


def clinic_registry(tenant_id: str | None = None) -> dict[str, Any]:
    ensure_multi_tenant_foundation()
    q = ClinicProfile.query
    if tenant_id:
        q = q.filter_by(tenant_id=tenant_id)
    rows = _safe(lambda: q.order_by(ClinicProfile.name.asc()).all(), [])
    return {
        "report": "clinic_registry",
        "read_only": False,
        "count": len(rows),
        "clinics": [row.to_dict() for row in rows],
        "tenant_scoped": bool(tenant_id),
    }


def laboratory_registry(tenant_id: str | None = None) -> dict[str, Any]:
    ensure_multi_tenant_foundation()
    q = Laboratory.query
    if tenant_id:
        q = q.filter_by(tenant_id=tenant_id)
    rows = _safe(lambda: q.order_by(Laboratory.name.asc()).all(), [])
    return {
        "report": "laboratory_registry",
        "read_only": False,
        "count": len(rows),
        "laboratories": [row.to_dict() for row in rows],
        "tenant_scoped": bool(tenant_id),
    }


def organization_settings(tenant_id: str | None = None) -> dict[str, Any]:
    ensure_multi_tenant_foundation()
    q = TenantOrganizationSetting.query
    if tenant_id:
        q = q.filter_by(tenant_id=tenant_id)
    rows = _safe(lambda: q.order_by(TenantOrganizationSetting.category.asc()).all(), [])
    return {
        "report": "organization_settings",
        "read_only": False,
        "count": len(rows),
        "settings": [row.to_dict() for row in rows],
    }


def tenant_resolver_status() -> dict[str, Any]:
    ensure_multi_tenant_foundation()
    tenant = EnterpriseTenant.query.first()
    sample = TenantResolver.resolve(tenant.tenant_code if tenant else None)
    return {
        "report": "tenant_resolver",
        "read_only": True,
        **TenantResolver.describe(),
        "sample_resolution": sample.to_dict(),
    }


def tenant_context_status() -> dict[str, Any]:
    ensure_multi_tenant_foundation()
    sample = TenantContext(
        tenant_id="example",
        tenant_code="TEN-EXAMPLE",
        tenant_name="Example Tenant",
        isolation_mode="STRICT",
        resolved=True,
        source="documentation",
    )
    return {
        "report": "tenant_context",
        "read_only": True,
        "context_fields": list(sample.to_dict().keys()),
        "sample": sample.to_dict(),
    }


def tenant_middleware_status() -> dict[str, Any]:
    ensure_multi_tenant_foundation()
    app = current_app._get_current_object()
    return {
        "report": "tenant_middleware",
        "read_only": True,
        "tenant_header": app.config.get("TENANT_ID_HEADER", "X-Tenant-ID"),
        "organization_header": app.config.get("ORGANIZATION_ID_HEADER", "X-Organization-ID"),
        "enforcement": "optional",
        "legacy_routes_unblocked": True,
        "registered": True,
    }


def tenant_admin_overview() -> dict[str, Any]:
    ensure_multi_tenant_foundation()
    overview = AdminEnterpriseService.overview()
    overview["report"] = "tenant_admin"
    overview["read_only"] = False
    return overview


def tenant_audit_log(tenant_id: str | None = None, limit: int = 50) -> dict[str, Any]:
    ensure_multi_tenant_foundation()
    payload = AuditEnterpriseService.list_records(tenant_id=tenant_id, limit=limit)
    payload["report"] = "tenant_audit"
    payload["read_only"] = True
    return payload


def tenant_isolation_framework() -> dict[str, Any]:
    ensure_multi_tenant_foundation()
    matrix = tenant_isolation_matrix()
    tenants = EnterpriseTenant.query.count()
    orgs = EnterpriseOrganization.query.count()
    clinics_bound = ClinicProfile.query.filter(ClinicProfile.tenant_id.isnot(None)).count()
    labs_bound = Laboratory.query.filter(Laboratory.tenant_id.isnot(None)).count()
    return {
        "report": "tenant_isolation_framework",
        "read_only": True,
        "tenants": tenants,
        "organizations": orgs,
        "clinics_tenant_bound": clinics_bound,
        "laboratories_tenant_bound": labs_bound,
        "isolation_checks": matrix.get("checks", []),
        "isolation_mode_default": "STRICT",
        "framework": {
            "header_resolution": True,
            "optional_middleware": True,
            "row_level_tenant_id": True,
            "schema_routing": "metadata_only",
        },
    }


def multi_tenant_dashboard() -> dict[str, Any]:
    ensure_multi_tenant_foundation()
    tenants = tenant_registry()
    orgs = organization_registry()
    clinics = clinic_registry()
    labs = laboratory_registry()
    settings = organization_settings()
    isolation = tenant_isolation_framework()
    return {
        "report": "multi_tenant_dashboard",
        "read_only": False,
        "status": "OK",
        "tenants_total": tenants.get("count", 0),
        "organizations_total": orgs.get("count", 0),
        "clinics_total": clinics.get("count", 0),
        "laboratories_total": labs.get("count", 0),
        "settings_total": settings.get("count", 0),
        "isolation_checks_passed": sum(
            1 for check in isolation.get("isolation_checks", []) if check.get("ok")
        ),
    }


def dashboard_payload() -> dict[str, Any]:
    ensure_multi_tenant_foundation()
    dash = multi_tenant_dashboard()
    return {
        "platform": "Multi Tenant Foundation",
        "phase": "7.1",
        "sprint": "Multi Tenant Foundation",
        "status": dash["status"],
        "read_only": False,
        "generated_at": datetime.utcnow().isoformat(),
        "summary": {
            "tenants_total": dash["tenants_total"],
            "organizations_total": dash["organizations_total"],
            "clinics_total": dash["clinics_total"],
            "laboratories_total": dash["laboratories_total"],
            "settings_total": dash["settings_total"],
            "isolation_checks_passed": dash["isolation_checks_passed"],
        },
        "features": list(FEATURES),
    }


def multi_tenant_readiness_report() -> dict[str, Any]:
    dashboard = dashboard_payload()
    return {
        "generated_at": datetime.utcnow().isoformat(),
        "phase": "7.1",
        "sprint": "Multi Tenant Foundation",
        "platform": dashboard["platform"],
        "status": dashboard["status"],
        "summary": dashboard["summary"],
        "features": list(FEATURES),
        "sections": {
            "tenant": tenant_registry(),
            "organization": organization_registry(),
            "clinic": clinic_registry(),
            "laboratory": laboratory_registry(),
            "organization_settings": organization_settings(),
            "tenant_resolver": tenant_resolver_status(),
            "tenant_context": tenant_context_status(),
            "tenant_middleware": tenant_middleware_status(),
            "tenant_admin": tenant_admin_overview(),
            "tenant_audit": tenant_audit_log(),
            "tenant_isolation_framework": tenant_isolation_framework(),
        },
        "legacy_routes": [
            "/tenant-isolation",
            "/api/v1/tenant-isolation/dashboard",
            "/api/v1/tenants",
            "/tenants",
        ],
        "architecture_doc": "docs/architecture/TENANT_ARCHITECTURE.md",
    }
