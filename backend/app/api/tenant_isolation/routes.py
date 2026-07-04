"""Tenant Isolation API routes — Phase 5 Sprint 5.4."""

from __future__ import annotations

from flask import Blueprint

from app.services.tenant_isolation_service import (
    clinic_a,
    clinic_b,
    clinic_c,
    dashboard_payload,
    one_platform,
    tenant_isolation_dashboard,
    tenant_isolation_matrix,
    tenant_isolation_readiness_report,
)

tenant_isolation_bp = Blueprint(
    "tenant_isolation_api",
    __name__,
    url_prefix="/api/v1/tenant-isolation",
)


@tenant_isolation_bp.route("/dashboard", methods=["GET"])
def tenant_isolation_dashboard_api():
    return dashboard_payload()


@tenant_isolation_bp.route("/platform", methods=["GET"])
def tenant_isolation_platform_api():
    return one_platform()


@tenant_isolation_bp.route("/clinic-a", methods=["GET"])
def tenant_isolation_clinic_a_api():
    return clinic_a()


@tenant_isolation_bp.route("/clinic-b", methods=["GET"])
def tenant_isolation_clinic_b_api():
    return clinic_b()


@tenant_isolation_bp.route("/clinic-c", methods=["GET"])
def tenant_isolation_clinic_c_api():
    return clinic_c()


@tenant_isolation_bp.route("/isolation", methods=["GET"])
def tenant_isolation_matrix_api():
    return tenant_isolation_matrix()


@tenant_isolation_bp.route("/inventory", methods=["GET"])
def tenant_isolation_inventory_api():
    return tenant_isolation_dashboard()


@tenant_isolation_bp.route("/readiness", methods=["GET"])
def tenant_isolation_readiness_api():
    return tenant_isolation_readiness_report()
