"""Healthcare Ecosystem API routes — Phase 10."""

from __future__ import annotations

from flask import Blueprint

from app.services.healthcare_ecosystem_service import (
    dashboard_payload,
    dxcon_lab,
    dxcon_clinic,
    dxcon_home,
    dxcon_pharmacy,
    dxcon_insurance,
    dxcon_ai,
    dxcon_cloud,
    dxcon_marketplace,
    partner_portal,
    customer_portal,
    enterprise_governance,
    architecture_board,
    release_board,
    medical_governance,
    security_governance,
    ai_governance,
    enterprise_audit,
    customer_success_portal,
    training_center,
    certification_center,
    release_manager,
    license_manager,
    commercial_readiness,
    support_center,
    knowledge_base,
    healthcare_ecosystem_readiness_report,
)

healthcare_ecosystem_bp = Blueprint("healthcare_ecosystem_api", __name__, url_prefix="/api/v1/healthcare-ecosystem")

@healthcare_ecosystem_bp.route("/dashboard", methods=["GET"])
def healthcare_ecosystem_dashboard_api():
    return dashboard_payload()

@healthcare_ecosystem_bp.route("/dxcon-lab", methods=["GET"])
def healthcare_ecosystem_dxcon_lab_api():
    return dxcon_lab()

@healthcare_ecosystem_bp.route("/dxcon-clinic", methods=["GET"])
def healthcare_ecosystem_dxcon_clinic_api():
    return dxcon_clinic()

@healthcare_ecosystem_bp.route("/dxcon-home", methods=["GET"])
def healthcare_ecosystem_dxcon_home_api():
    return dxcon_home()

@healthcare_ecosystem_bp.route("/dxcon-pharmacy", methods=["GET"])
def healthcare_ecosystem_dxcon_pharmacy_api():
    return dxcon_pharmacy()

@healthcare_ecosystem_bp.route("/dxcon-insurance", methods=["GET"])
def healthcare_ecosystem_dxcon_insurance_api():
    return dxcon_insurance()

@healthcare_ecosystem_bp.route("/dxcon-ai", methods=["GET"])
def healthcare_ecosystem_dxcon_ai_api():
    return dxcon_ai()

@healthcare_ecosystem_bp.route("/dxcon-cloud", methods=["GET"])
def healthcare_ecosystem_dxcon_cloud_api():
    return dxcon_cloud()

@healthcare_ecosystem_bp.route("/dxcon-marketplace", methods=["GET"])
def healthcare_ecosystem_dxcon_marketplace_api():
    return dxcon_marketplace()

@healthcare_ecosystem_bp.route("/partner-portal", methods=["GET"])
def healthcare_ecosystem_partner_portal_api():
    return partner_portal()

@healthcare_ecosystem_bp.route("/customer-portal", methods=["GET"])
def healthcare_ecosystem_customer_portal_api():
    return customer_portal()

@healthcare_ecosystem_bp.route("/enterprise-governance", methods=["GET"])
def healthcare_ecosystem_enterprise_governance_api():
    return enterprise_governance()

@healthcare_ecosystem_bp.route("/architecture-board", methods=["GET"])
def healthcare_ecosystem_architecture_board_api():
    return architecture_board()

@healthcare_ecosystem_bp.route("/release-board", methods=["GET"])
def healthcare_ecosystem_release_board_api():
    return release_board()

@healthcare_ecosystem_bp.route("/medical-governance", methods=["GET"])
def healthcare_ecosystem_medical_governance_api():
    return medical_governance()

@healthcare_ecosystem_bp.route("/security-governance", methods=["GET"])
def healthcare_ecosystem_security_governance_api():
    return security_governance()

@healthcare_ecosystem_bp.route("/ai-governance", methods=["GET"])
def healthcare_ecosystem_ai_governance_api():
    return ai_governance()

@healthcare_ecosystem_bp.route("/enterprise-audit", methods=["GET"])
def healthcare_ecosystem_enterprise_audit_api():
    return enterprise_audit()

@healthcare_ecosystem_bp.route("/customer-success", methods=["GET"])
def healthcare_ecosystem_customer_success_portal_api():
    return customer_success_portal()

@healthcare_ecosystem_bp.route("/training-center", methods=["GET"])
def healthcare_ecosystem_training_center_api():
    return training_center()

@healthcare_ecosystem_bp.route("/certification-center", methods=["GET"])
def healthcare_ecosystem_certification_center_api():
    return certification_center()

@healthcare_ecosystem_bp.route("/release-manager", methods=["GET"])
def healthcare_ecosystem_release_manager_api():
    return release_manager()

@healthcare_ecosystem_bp.route("/license-manager", methods=["GET"])
def healthcare_ecosystem_license_manager_api():
    return license_manager()

@healthcare_ecosystem_bp.route("/commercial-readiness", methods=["GET"])
def healthcare_ecosystem_commercial_readiness_api():
    return commercial_readiness()

@healthcare_ecosystem_bp.route("/support-center", methods=["GET"])
def healthcare_ecosystem_support_center_api():
    return support_center()

@healthcare_ecosystem_bp.route("/knowledge-base", methods=["GET"])
def healthcare_ecosystem_knowledge_base_api():
    return knowledge_base()

@healthcare_ecosystem_bp.route("/readiness", methods=["GET"])
def healthcare_ecosystem_readiness_api():
    return healthcare_ecosystem_readiness_report()
