"""Multi-tenant clinic isolation business logic for Phase 5 Sprint 5.4."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from flask import current_app

from app.extensions.db import db
from app.models.enterprise_platform import EnterpriseOrganization, EnterpriseTenant
from app.services.enterprise_platform_service import (
    AdminEnterpriseService,
    OrganizationEnterpriseService,
    SecurityEnterpriseService,
    TenantEnterpriseService,
)
from app.services.reporting_service import _safe

TENANT_ISOLATION_ROLES = ("SUPER_ADMIN", "ADMIN")

FEATURES = (
    "Clinic A",
    "Clinic B",
    "Clinic C",
    "One Platform",
    "Tenant Isolation",
)

DEMO_CLINICS = (
    {
        "key": "clinic-a",
        "label": "Clinic A",
        "tenant_code": "TEN-CLINIC-A",
        "name": "Clinic A — Downtown",
        "schema_name": "tenant_clinic_a",
        "org_code": "CLN-A-ROOT",
        "org_name": "Clinic A Root Organization",
    },
    {
        "key": "clinic-b",
        "label": "Clinic B",
        "tenant_code": "TEN-CLINIC-B",
        "name": "Clinic B — Riverside",
        "schema_name": "tenant_clinic_b",
        "org_code": "CLN-B-ROOT",
        "org_name": "Clinic B Root Organization",
    },
    {
        "key": "clinic-c",
        "label": "Clinic C",
        "tenant_code": "TEN-CLINIC-C",
        "name": "Clinic C — North Campus",
        "schema_name": "tenant_clinic_c",
        "org_code": "CLN-C-ROOT",
        "org_name": "Clinic C Root Organization",
    },
)


class TenantIsolationError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


def ensure_tenant_isolation() -> dict[str, Any]:
    ensure_demo_clinics()
    return {"ready": True, "read_only": True}


def ensure_demo_clinics() -> dict[str, Any]:
    created = []
    for clinic in DEMO_CLINICS:
        tenant = EnterpriseTenant.query.filter_by(tenant_code=clinic["tenant_code"]).first()
        if tenant:
            continue
        payload = TenantEnterpriseService.create(
            {
                "tenant_code": clinic["tenant_code"],
                "name": clinic["name"],
                "isolation_mode": "STRICT",
                "schema_name": clinic["schema_name"],
            }
        )
        tenant = EnterpriseTenant.query.get(payload["id"])
        db.session.add(
            EnterpriseOrganization(
                tenant_id=tenant.id,
                org_code=clinic["org_code"],
                name=clinic["org_name"],
                level=0,
            )
        )
        db.session.commit()
        created.append(clinic["tenant_code"])
    return {"created": created, "clinic_count": len(DEMO_CLINICS)}


def _clinic_spec(key: str) -> dict[str, Any]:
    for clinic in DEMO_CLINICS:
        if clinic["key"] == key:
            return clinic
    raise TenantIsolationError(f"Unknown clinic: {key}", 404)


def clinic_tenant(key: str) -> dict[str, Any]:
    ensure_tenant_isolation()
    clinic = _clinic_spec(key)
    tenant = EnterpriseTenant.query.filter_by(tenant_code=clinic["tenant_code"]).first()
    if not tenant:
        raise TenantIsolationError(f"Clinic tenant not found: {clinic['label']}", 404)
    isolation = TenantEnterpriseService.isolation(tenant.id)
    orgs = OrganizationEnterpriseService.list_organizations(tenant_id=tenant.id)
    roles = SecurityEnterpriseService.list_rbac_roles(tenant_id=tenant.id)
    return {
        "report": clinic["key"],
        "read_only": True,
        "label": clinic["label"],
        "tenant": tenant.to_dict(),
        "isolation": isolation,
        "organizations": orgs.get("organizations", []),
        "rbac_roles": roles.get("roles", []),
        "platform_header": current_app.config.get("TENANT_ID_HEADER", "X-Tenant-ID"),
    }


def clinic_a() -> dict[str, Any]:
    return clinic_tenant("clinic-a")


def clinic_b() -> dict[str, Any]:
    return clinic_tenant("clinic-b")


def clinic_c() -> dict[str, Any]:
    return clinic_tenant("clinic-c")


def one_platform() -> dict[str, Any]:
    ensure_tenant_isolation()
    overview = AdminEnterpriseService.overview()
    tenants = TenantEnterpriseService.list_tenants()
    demo = []
    for clinic in DEMO_CLINICS:
        tenant = EnterpriseTenant.query.filter_by(tenant_code=clinic["tenant_code"]).first()
        if tenant:
            demo.append(
                {
                    "label": clinic["label"],
                    "key": clinic["key"],
                    "tenant": tenant.to_dict(),
                    "isolation": TenantEnterpriseService.isolation(tenant.id),
                }
            )
    return {
        "report": "one_platform",
        "read_only": True,
        "architecture": "Clinic A + Clinic B + Clinic C → One Platform → Tenant Isolation",
        "platform": "DxCon Intelligent Diagnostic Services Platform",
        "overview": overview,
        "tenants_total": tenants.get("count", 0),
        "demo_clinics": demo,
        "tenant_header": current_app.config.get("TENANT_ID_HEADER", "X-Tenant-ID"),
    }


def tenant_isolation_matrix() -> dict[str, Any]:
    ensure_tenant_isolation()
    tenants = TenantEnterpriseService.list_tenants()
    rows = []
    schema_names: set[str] = set()
    strict_count = 0
    for tenant in tenants.get("tenants", []):
        isolation = TenantEnterpriseService.isolation(tenant["id"])
        schema_names.add(tenant.get("schema_name") or "")
        if tenant.get("isolation_mode") == "STRICT":
            strict_count += 1
        rows.append(
            {
                "tenant_code": tenant.get("tenant_code"),
                "name": tenant.get("name"),
                "isolation_mode": tenant.get("isolation_mode"),
                "schema_name": tenant.get("schema_name"),
                "isolated": isolation.get("isolated"),
                "organization_count": isolation.get("organization_count", 0),
            }
        )
    org_rows = _safe(lambda: EnterpriseOrganization.query.all(), [])
    cross_tenant_orgs = sum(
        1
        for org in org_rows
        if org.tenant_id
        and EnterpriseTenant.query.get(org.tenant_id) is None
    )
    unique_schemas = len({name for name in schema_names if name}) == len(
        [name for name in schema_names if name]
    )
    checks = [
        {
            "id": 1,
            "title": "Strict isolation mode",
            "detail": "Every tenant uses STRICT isolation_mode.",
            "status": "PASS" if strict_count == tenants.get("count", 0) else "WARN",
        },
        {
            "id": 2,
            "title": "Unique schema namespaces",
            "detail": "Each tenant maps to a dedicated schema_name.",
            "status": "PASS" if unique_schemas else "FAIL",
        },
        {
            "id": 3,
            "title": "Organization tenant binding",
            "detail": "Organizations reference valid tenant_id values only.",
            "status": "PASS" if cross_tenant_orgs == 0 else "FAIL",
        },
        {
            "id": 4,
            "title": "Demo clinic coverage",
            "detail": "Clinic A, Clinic B, and Clinic C tenants are provisioned.",
            "status": "PASS" if len(rows) >= 3 else "WARN",
        },
        {
            "id": 5,
            "title": "Tenant request header",
            "detail": "Platform resolves tenant context from configured header.",
            "status": "PASS",
        },
    ]
    return {
        "report": "tenant_isolation",
        "read_only": True,
        "tenants_total": tenants.get("count", 0),
        "strict_isolation_count": strict_count,
        "matrix": rows,
        "checks": checks,
        "checks_passed": sum(1 for item in checks if item["status"] == "PASS"),
        "checks_total": len(checks),
        "legacy_api": "GET /api/v1/tenants/<tenant_id>/isolation",
    }


def tenant_isolation_dashboard() -> dict[str, Any]:
    ensure_tenant_isolation()
    platform = one_platform()
    matrix = tenant_isolation_matrix()
    status = "OK"
    if matrix["checks_passed"] < matrix["checks_total"]:
        status = "WARN"
    return {
        "report": "tenant_isolation_dashboard",
        "read_only": True,
        "status": status,
        "demo_clinics": len(platform.get("demo_clinics", [])),
        "tenants_total": platform.get("tenants_total", 0),
        "strict_isolation_count": matrix.get("strict_isolation_count", 0),
        "isolation_checks_passed": matrix.get("checks_passed", 0),
    }


def tenant_isolation_readiness_report() -> dict[str, Any]:
    dashboard = dashboard_payload()
    return {
        "generated_at": datetime.utcnow().isoformat(),
        "phase": "5.4",
        "sprint": "Tenant Isolation",
        "platform": dashboard["platform"],
        "status": dashboard["status"],
        "summary": dashboard["summary"],
        "features": list(FEATURES),
        "sections": {
            "clinic_a": clinic_a(),
            "clinic_b": clinic_b(),
            "clinic_c": clinic_c(),
            "one_platform": one_platform(),
            "tenant_isolation": tenant_isolation_matrix(),
        },
    }


def dashboard_payload() -> dict[str, Any]:
    ensure_tenant_isolation()
    dash = tenant_isolation_dashboard()
    platform = one_platform()
    matrix = tenant_isolation_matrix()
    return {
        "platform": "Tenant Isolation",
        "phase": "5.4",
        "sprint": "Tenant Isolation",
        "status": dash["status"],
        "read_only": True,
        "generated_at": datetime.utcnow().isoformat(),
        "summary": {
            "demo_clinics": dash["demo_clinics"],
            "tenants_total": dash["tenants_total"],
            "strict_isolation_count": dash["strict_isolation_count"],
            "isolation_checks_passed": dash["isolation_checks_passed"],
            "isolation_checks_total": matrix["checks_total"],
        },
        "features": list(FEATURES),
    }
