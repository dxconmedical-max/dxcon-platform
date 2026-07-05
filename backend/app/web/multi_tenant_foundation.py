"""Multi Tenant Foundation web routes — Phase 7.1."""

from __future__ import annotations

from flask import Blueprint

from app.services.multi_tenant_foundation_service import MULTI_TENANT_ROLES
from app.utils.auth import role_required
from app.web.multi_tenant_foundation_lib import (
    build_admin_body,
    build_audit_body,
    build_clinics_body,
    build_context_body,
    build_dashboard_body,
    build_isolation_body,
    build_laboratories_body,
    build_middleware_body,
    build_organizations_body,
    build_resolver_body,
    build_settings_body,
    build_tenants_body,
    render_mtf_page,
)

multi_tenant_foundation_web_bp = Blueprint("multi_tenant_foundation_web", __name__)


@multi_tenant_foundation_web_bp.route("/multi-tenant")
@role_required(*MULTI_TENANT_ROLES)
def multi_tenant_dashboard():
    return render_mtf_page("Multi Tenant Foundation", build_dashboard_body())


@multi_tenant_foundation_web_bp.route("/multi-tenant/tenants")
@role_required(*MULTI_TENANT_ROLES)
def multi_tenant_tenants():
    return render_mtf_page("Tenants", build_tenants_body())


@multi_tenant_foundation_web_bp.route("/multi-tenant/organizations")
@role_required(*MULTI_TENANT_ROLES)
def multi_tenant_organizations():
    return render_mtf_page("Organizations", build_organizations_body())


@multi_tenant_foundation_web_bp.route("/multi-tenant/clinics")
@role_required(*MULTI_TENANT_ROLES)
def multi_tenant_clinics():
    return render_mtf_page("Clinics", build_clinics_body())


@multi_tenant_foundation_web_bp.route("/multi-tenant/laboratories")
@role_required(*MULTI_TENANT_ROLES)
def multi_tenant_laboratories():
    return render_mtf_page("Laboratories", build_laboratories_body())


@multi_tenant_foundation_web_bp.route("/multi-tenant/settings")
@role_required(*MULTI_TENANT_ROLES)
def multi_tenant_settings():
    return render_mtf_page("Organization Settings", build_settings_body())


@multi_tenant_foundation_web_bp.route("/multi-tenant/resolver")
@role_required(*MULTI_TENANT_ROLES)
def multi_tenant_resolver():
    return render_mtf_page("Tenant Resolver", build_resolver_body())


@multi_tenant_foundation_web_bp.route("/multi-tenant/context")
@role_required(*MULTI_TENANT_ROLES)
def multi_tenant_context():
    return render_mtf_page("Tenant Context", build_context_body())


@multi_tenant_foundation_web_bp.route("/multi-tenant/middleware")
@role_required(*MULTI_TENANT_ROLES)
def multi_tenant_middleware():
    return render_mtf_page("Tenant Middleware", build_middleware_body())


@multi_tenant_foundation_web_bp.route("/multi-tenant/admin")
@role_required(*MULTI_TENANT_ROLES)
def multi_tenant_admin():
    return render_mtf_page("Tenant Admin", build_admin_body())


@multi_tenant_foundation_web_bp.route("/multi-tenant/audit")
@role_required(*MULTI_TENANT_ROLES)
def multi_tenant_audit():
    return render_mtf_page("Tenant Audit", build_audit_body())


@multi_tenant_foundation_web_bp.route("/multi-tenant/isolation")
@role_required(*MULTI_TENANT_ROLES)
def multi_tenant_isolation():
    return render_mtf_page("Tenant Isolation", build_isolation_body())
