"""Tenant Isolation web routes — Phase 5 Sprint 5.4."""

from __future__ import annotations

from flask import Blueprint

from app.services.tenant_isolation_service import TENANT_ISOLATION_ROLES
from app.utils.auth import role_required
from app.web.tenant_isolation_lib import (
    build_clinic_body,
    build_isolation_body,
    build_platform_body,
    render_tenant_page,
)

tenant_isolation_web_bp = Blueprint("tenant_isolation_web", __name__)


@tenant_isolation_web_bp.route("/tenant-isolation")
@role_required(*TENANT_ISOLATION_ROLES)
def tenant_isolation_platform():
    return render_tenant_page("One Platform", build_platform_body())


@tenant_isolation_web_bp.route("/tenant-isolation/clinic-a")
@role_required(*TENANT_ISOLATION_ROLES)
def tenant_isolation_clinic_a():
    return render_tenant_page("Clinic A", build_clinic_body("clinic-a"))


@tenant_isolation_web_bp.route("/tenant-isolation/clinic-b")
@role_required(*TENANT_ISOLATION_ROLES)
def tenant_isolation_clinic_b():
    return render_tenant_page("Clinic B", build_clinic_body("clinic-b"))


@tenant_isolation_web_bp.route("/tenant-isolation/clinic-c")
@role_required(*TENANT_ISOLATION_ROLES)
def tenant_isolation_clinic_c():
    return render_tenant_page("Clinic C", build_clinic_body("clinic-c"))


@tenant_isolation_web_bp.route("/tenant-isolation/isolation")
@role_required(*TENANT_ISOLATION_ROLES)
def tenant_isolation_matrix_page():
    return render_tenant_page("Tenant Isolation", build_isolation_body())
