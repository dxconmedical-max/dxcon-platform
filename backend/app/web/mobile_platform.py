"""Mobile Platform web routes — Phase 7.4."""

from __future__ import annotations

from flask import Blueprint

from app.services.mobile_platform_service import MOBILE_PLATFORM_ROLES
from app.utils.auth import role_required
from app.web.mobile_platform_lib import (
    build_dashboard_body,
    build_collector_api_body,
    build_doctor_api_body,
    build_patient_api_body,
    build_notification_api_body,
    build_offline_sync_api_body,
    build_token_refresh_body,
    build_conflict_resolution_body,
    build_pwa_manifest_body,
    render_hub_page,
)

mobile_platform_web_bp = Blueprint("mobile_platform_web", __name__)

@mobile_platform_web_bp.route("/mobile-platform")
@role_required(*MOBILE_PLATFORM_ROLES)
def mobile_platform_dashboard():
    return render_hub_page("Mobile Platform", build_dashboard_body())
@mobile_platform_web_bp.route("/mobile-platform/collector-api")
@role_required(*MOBILE_PLATFORM_ROLES)
def mobile_platform_collector_api():
    return render_hub_page("Collector API", build_collector_api_body())
@mobile_platform_web_bp.route("/mobile-platform/doctor-api")
@role_required(*MOBILE_PLATFORM_ROLES)
def mobile_platform_doctor_api():
    return render_hub_page("Doctor API", build_doctor_api_body())
@mobile_platform_web_bp.route("/mobile-platform/patient-api")
@role_required(*MOBILE_PLATFORM_ROLES)
def mobile_platform_patient_api():
    return render_hub_page("Patient API", build_patient_api_body())
@mobile_platform_web_bp.route("/mobile-platform/notifications")
@role_required(*MOBILE_PLATFORM_ROLES)
def mobile_platform_notification_api():
    return render_hub_page("Notification API", build_notification_api_body())
@mobile_platform_web_bp.route("/mobile-platform/offline-sync")
@role_required(*MOBILE_PLATFORM_ROLES)
def mobile_platform_offline_sync_api():
    return render_hub_page("Offline Sync API", build_offline_sync_api_body())
@mobile_platform_web_bp.route("/mobile-platform/token-refresh")
@role_required(*MOBILE_PLATFORM_ROLES)
def mobile_platform_token_refresh():
    return render_hub_page("Token Refresh", build_token_refresh_body())
@mobile_platform_web_bp.route("/mobile-platform/conflict-resolution")
@role_required(*MOBILE_PLATFORM_ROLES)
def mobile_platform_conflict_resolution():
    return render_hub_page("Conflict Resolution", build_conflict_resolution_body())
@mobile_platform_web_bp.route("/mobile-platform/pwa-manifest")
@role_required(*MOBILE_PLATFORM_ROLES)
def mobile_platform_pwa_manifest():
    return render_hub_page("PWA Manifest", build_pwa_manifest_body())

