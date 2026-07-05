"""Mobile Platform API routes — Phase 7.4."""

from __future__ import annotations

from flask import Blueprint

from app.services.mobile_platform_service import (
    dashboard_payload,
    collector_api,
    doctor_api,
    patient_api,
    notification_api,
    offline_sync_api,
    token_refresh,
    conflict_resolution,
    pwa_manifest,
    mobile_platform_readiness_report,
)

mobile_platform_bp = Blueprint("mobile_platform_api", __name__, url_prefix="/api/v1/mobile-platform")

@mobile_platform_bp.route("/dashboard", methods=["GET"])
def mobile_platform_dashboard_api():
    return dashboard_payload()

@mobile_platform_bp.route("/collector-api", methods=["GET"])
def mobile_platform_collector_api_api():
    return collector_api()

@mobile_platform_bp.route("/doctor-api", methods=["GET"])
def mobile_platform_doctor_api_api():
    return doctor_api()

@mobile_platform_bp.route("/patient-api", methods=["GET"])
def mobile_platform_patient_api_api():
    return patient_api()

@mobile_platform_bp.route("/notifications", methods=["GET"])
def mobile_platform_notification_api_api():
    return notification_api()

@mobile_platform_bp.route("/offline-sync", methods=["GET"])
def mobile_platform_offline_sync_api_api():
    return offline_sync_api()

@mobile_platform_bp.route("/token-refresh", methods=["GET"])
def mobile_platform_token_refresh_api():
    return token_refresh()

@mobile_platform_bp.route("/conflict-resolution", methods=["GET"])
def mobile_platform_conflict_resolution_api():
    return conflict_resolution()

@mobile_platform_bp.route("/pwa-manifest", methods=["GET"])
def mobile_platform_pwa_manifest_api():
    return pwa_manifest()

@mobile_platform_bp.route("/readiness", methods=["GET"])
def mobile_platform_readiness_api():
    return mobile_platform_readiness_report()
