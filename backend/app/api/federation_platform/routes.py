"""Federation Platform API routes — Phase 7.10."""

from __future__ import annotations

from flask import Blueprint

from app.services.federation_platform_service import (
    dashboard_payload,
    regional_hub,
    national_hub,
    clinic_federation,
    laboratory_federation,
    cross_organization_exchange,
    sync_queue,
    federation_audit,
    federation_platform_readiness_report,
)

federation_platform_bp = Blueprint("federation_platform_api", __name__, url_prefix="/api/v1/federation-platform")

@federation_platform_bp.route("/dashboard", methods=["GET"])
def federation_platform_dashboard_api():
    return dashboard_payload()

@federation_platform_bp.route("/regional", methods=["GET"])
def federation_platform_regional_hub_api():
    return regional_hub()

@federation_platform_bp.route("/national", methods=["GET"])
def federation_platform_national_hub_api():
    return national_hub()

@federation_platform_bp.route("/clinic-federation", methods=["GET"])
def federation_platform_clinic_federation_api():
    return clinic_federation()

@federation_platform_bp.route("/lab-federation", methods=["GET"])
def federation_platform_laboratory_federation_api():
    return laboratory_federation()

@federation_platform_bp.route("/exchange", methods=["GET"])
def federation_platform_cross_organization_exchange_api():
    return cross_organization_exchange()

@federation_platform_bp.route("/sync-queue", methods=["GET"])
def federation_platform_sync_queue_api():
    return sync_queue()

@federation_platform_bp.route("/audit", methods=["GET"])
def federation_platform_federation_audit_api():
    return federation_audit()

@federation_platform_bp.route("/readiness", methods=["GET"])
def federation_platform_readiness_api():
    return federation_platform_readiness_report()
