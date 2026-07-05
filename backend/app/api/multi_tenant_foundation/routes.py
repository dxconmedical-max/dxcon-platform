"""Multi Tenant Foundation API routes — Phase 7.1."""

from __future__ import annotations

from flask import Blueprint, request

from app.services.multi_tenant_foundation_service import (
    clinic_registry,
    dashboard_payload,
    laboratory_registry,
    multi_tenant_readiness_report,
    organization_registry,
    organization_settings,
    tenant_admin_overview,
    tenant_audit_log,
    tenant_context_status,
    tenant_isolation_framework,
    tenant_middleware_status,
    tenant_registry,
    tenant_resolver_status,
)

multi_tenant_foundation_bp = Blueprint(
    "multi_tenant_foundation_api",
    __name__,
    url_prefix="/api/v1/multi-tenant",
)


def _tenant_id():
    return request.args.get("tenant_id")


@multi_tenant_foundation_bp.route("/dashboard", methods=["GET"])
def multi_tenant_dashboard_api():
    return dashboard_payload()


@multi_tenant_foundation_bp.route("/tenants", methods=["GET"])
def multi_tenant_tenants_api():
    return tenant_registry()


@multi_tenant_foundation_bp.route("/organizations", methods=["GET"])
def multi_tenant_organizations_api():
    return organization_registry(_tenant_id())


@multi_tenant_foundation_bp.route("/clinics", methods=["GET"])
def multi_tenant_clinics_api():
    return clinic_registry(_tenant_id())


@multi_tenant_foundation_bp.route("/laboratories", methods=["GET"])
def multi_tenant_laboratories_api():
    return laboratory_registry(_tenant_id())


@multi_tenant_foundation_bp.route("/settings", methods=["GET"])
def multi_tenant_settings_api():
    return organization_settings(_tenant_id())


@multi_tenant_foundation_bp.route("/resolver", methods=["GET"])
def multi_tenant_resolver_api():
    return tenant_resolver_status()


@multi_tenant_foundation_bp.route("/context", methods=["GET"])
def multi_tenant_context_api():
    return tenant_context_status()


@multi_tenant_foundation_bp.route("/middleware", methods=["GET"])
def multi_tenant_middleware_api():
    return tenant_middleware_status()


@multi_tenant_foundation_bp.route("/admin", methods=["GET"])
def multi_tenant_admin_api():
    return tenant_admin_overview()


@multi_tenant_foundation_bp.route("/audit", methods=["GET"])
def multi_tenant_audit_api():
    return tenant_audit_log(_tenant_id())


@multi_tenant_foundation_bp.route("/isolation", methods=["GET"])
def multi_tenant_isolation_api():
    return tenant_isolation_framework()


@multi_tenant_foundation_bp.route("/readiness", methods=["GET"])
def multi_tenant_readiness_api():
    return multi_tenant_readiness_report()
