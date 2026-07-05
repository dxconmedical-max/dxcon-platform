"""Federation Platform web routes — Phase 7.10."""

from __future__ import annotations

from flask import Blueprint

from app.services.federation_platform_service import FEDERATION_PLATFORM_ROLES
from app.utils.auth import role_required
from app.web.federation_platform_lib import (
    build_dashboard_body,
    build_regional_hub_body,
    build_national_hub_body,
    build_clinic_federation_body,
    build_laboratory_federation_body,
    build_cross_organization_exchange_body,
    build_sync_queue_body,
    build_federation_audit_body,
    render_hub_page,
)

federation_platform_web_bp = Blueprint("federation_platform_web", __name__)

@federation_platform_web_bp.route("/federation-platform")
@role_required(*FEDERATION_PLATFORM_ROLES)
def federation_platform_dashboard():
    return render_hub_page("Federation Platform", build_dashboard_body())
@federation_platform_web_bp.route("/federation-platform/regional")
@role_required(*FEDERATION_PLATFORM_ROLES)
def federation_platform_regional_hub():
    return render_hub_page("Regional Hub", build_regional_hub_body())
@federation_platform_web_bp.route("/federation-platform/national")
@role_required(*FEDERATION_PLATFORM_ROLES)
def federation_platform_national_hub():
    return render_hub_page("National Hub", build_national_hub_body())
@federation_platform_web_bp.route("/federation-platform/clinic-federation")
@role_required(*FEDERATION_PLATFORM_ROLES)
def federation_platform_clinic_federation():
    return render_hub_page("Clinic Federation", build_clinic_federation_body())
@federation_platform_web_bp.route("/federation-platform/lab-federation")
@role_required(*FEDERATION_PLATFORM_ROLES)
def federation_platform_laboratory_federation():
    return render_hub_page("Laboratory Federation", build_laboratory_federation_body())
@federation_platform_web_bp.route("/federation-platform/exchange")
@role_required(*FEDERATION_PLATFORM_ROLES)
def federation_platform_cross_organization_exchange():
    return render_hub_page("Cross Organization Exchange", build_cross_organization_exchange_body())
@federation_platform_web_bp.route("/federation-platform/sync-queue")
@role_required(*FEDERATION_PLATFORM_ROLES)
def federation_platform_sync_queue():
    return render_hub_page("Sync Queue", build_sync_queue_body())
@federation_platform_web_bp.route("/federation-platform/audit")
@role_required(*FEDERATION_PLATFORM_ROLES)
def federation_platform_federation_audit():
    return render_hub_page("Federation Audit", build_federation_audit_body())

