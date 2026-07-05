"""Healthcare Ecosystem web routes — Phase 10."""

from __future__ import annotations

from flask import Blueprint

from app.services.healthcare_ecosystem_service import HEALTHCARE_ECOSYSTEM_ROLES
from app.utils.auth import role_required
from app.web.healthcare_ecosystem_lib import (
    build_dashboard_body,
    build_dxcon_lab_body,
    build_dxcon_clinic_body,
    build_dxcon_home_body,
    build_dxcon_pharmacy_body,
    build_dxcon_insurance_body,
    build_dxcon_ai_body,
    build_dxcon_cloud_body,
    build_dxcon_marketplace_body,
    build_partner_portal_body,
    build_customer_portal_body,
    build_enterprise_governance_body,
    build_architecture_board_body,
    build_release_board_body,
    build_medical_governance_body,
    build_security_governance_body,
    build_ai_governance_body,
    build_enterprise_audit_body,
    build_customer_success_portal_body,
    build_training_center_body,
    build_certification_center_body,
    build_release_manager_body,
    build_license_manager_body,
    build_commercial_readiness_body,
    build_support_center_body,
    build_knowledge_base_body,
    render_hub_page,
)

healthcare_ecosystem_web_bp = Blueprint("healthcare_ecosystem_web", __name__)

@healthcare_ecosystem_web_bp.route("/healthcare-ecosystem")
@role_required(*HEALTHCARE_ECOSYSTEM_ROLES)
def healthcare_ecosystem_dashboard():
    return render_hub_page("Healthcare Ecosystem", build_dashboard_body())
@healthcare_ecosystem_web_bp.route("/healthcare-ecosystem/dxcon-lab")
@role_required(*HEALTHCARE_ECOSYSTEM_ROLES)
def healthcare_ecosystem_dxcon_lab():
    return render_hub_page("DxCon Lab", build_dxcon_lab_body())
@healthcare_ecosystem_web_bp.route("/healthcare-ecosystem/dxcon-clinic")
@role_required(*HEALTHCARE_ECOSYSTEM_ROLES)
def healthcare_ecosystem_dxcon_clinic():
    return render_hub_page("DxCon Clinic", build_dxcon_clinic_body())
@healthcare_ecosystem_web_bp.route("/healthcare-ecosystem/dxcon-home")
@role_required(*HEALTHCARE_ECOSYSTEM_ROLES)
def healthcare_ecosystem_dxcon_home():
    return render_hub_page("DxCon Home", build_dxcon_home_body())
@healthcare_ecosystem_web_bp.route("/healthcare-ecosystem/dxcon-pharmacy")
@role_required(*HEALTHCARE_ECOSYSTEM_ROLES)
def healthcare_ecosystem_dxcon_pharmacy():
    return render_hub_page("DxCon Pharmacy", build_dxcon_pharmacy_body())
@healthcare_ecosystem_web_bp.route("/healthcare-ecosystem/dxcon-insurance")
@role_required(*HEALTHCARE_ECOSYSTEM_ROLES)
def healthcare_ecosystem_dxcon_insurance():
    return render_hub_page("DxCon Insurance", build_dxcon_insurance_body())
@healthcare_ecosystem_web_bp.route("/healthcare-ecosystem/dxcon-ai")
@role_required(*HEALTHCARE_ECOSYSTEM_ROLES)
def healthcare_ecosystem_dxcon_ai():
    return render_hub_page("DxCon AI", build_dxcon_ai_body())
@healthcare_ecosystem_web_bp.route("/healthcare-ecosystem/dxcon-cloud")
@role_required(*HEALTHCARE_ECOSYSTEM_ROLES)
def healthcare_ecosystem_dxcon_cloud():
    return render_hub_page("DxCon Cloud", build_dxcon_cloud_body())
@healthcare_ecosystem_web_bp.route("/healthcare-ecosystem/dxcon-marketplace")
@role_required(*HEALTHCARE_ECOSYSTEM_ROLES)
def healthcare_ecosystem_dxcon_marketplace():
    return render_hub_page("DxCon Marketplace", build_dxcon_marketplace_body())
@healthcare_ecosystem_web_bp.route("/healthcare-ecosystem/partner-portal")
@role_required(*HEALTHCARE_ECOSYSTEM_ROLES)
def healthcare_ecosystem_partner_portal():
    return render_hub_page("Partner Portal", build_partner_portal_body())
@healthcare_ecosystem_web_bp.route("/healthcare-ecosystem/customer-portal")
@role_required(*HEALTHCARE_ECOSYSTEM_ROLES)
def healthcare_ecosystem_customer_portal():
    return render_hub_page("Customer Portal", build_customer_portal_body())
@healthcare_ecosystem_web_bp.route("/healthcare-ecosystem/enterprise-governance")
@role_required(*HEALTHCARE_ECOSYSTEM_ROLES)
def healthcare_ecosystem_enterprise_governance():
    return render_hub_page("Enterprise Governance", build_enterprise_governance_body())
@healthcare_ecosystem_web_bp.route("/healthcare-ecosystem/architecture-board")
@role_required(*HEALTHCARE_ECOSYSTEM_ROLES)
def healthcare_ecosystem_architecture_board():
    return render_hub_page("Architecture Board", build_architecture_board_body())
@healthcare_ecosystem_web_bp.route("/healthcare-ecosystem/release-board")
@role_required(*HEALTHCARE_ECOSYSTEM_ROLES)
def healthcare_ecosystem_release_board():
    return render_hub_page("Release Board", build_release_board_body())
@healthcare_ecosystem_web_bp.route("/healthcare-ecosystem/medical-governance")
@role_required(*HEALTHCARE_ECOSYSTEM_ROLES)
def healthcare_ecosystem_medical_governance():
    return render_hub_page("Medical Governance", build_medical_governance_body())
@healthcare_ecosystem_web_bp.route("/healthcare-ecosystem/security-governance")
@role_required(*HEALTHCARE_ECOSYSTEM_ROLES)
def healthcare_ecosystem_security_governance():
    return render_hub_page("Security Governance", build_security_governance_body())
@healthcare_ecosystem_web_bp.route("/healthcare-ecosystem/ai-governance")
@role_required(*HEALTHCARE_ECOSYSTEM_ROLES)
def healthcare_ecosystem_ai_governance():
    return render_hub_page("AI Governance", build_ai_governance_body())
@healthcare_ecosystem_web_bp.route("/healthcare-ecosystem/enterprise-audit")
@role_required(*HEALTHCARE_ECOSYSTEM_ROLES)
def healthcare_ecosystem_enterprise_audit():
    return render_hub_page("Enterprise Audit", build_enterprise_audit_body())
@healthcare_ecosystem_web_bp.route("/healthcare-ecosystem/customer-success")
@role_required(*HEALTHCARE_ECOSYSTEM_ROLES)
def healthcare_ecosystem_customer_success_portal():
    return render_hub_page("Customer Success Portal", build_customer_success_portal_body())
@healthcare_ecosystem_web_bp.route("/healthcare-ecosystem/training-center")
@role_required(*HEALTHCARE_ECOSYSTEM_ROLES)
def healthcare_ecosystem_training_center():
    return render_hub_page("Training Center", build_training_center_body())
@healthcare_ecosystem_web_bp.route("/healthcare-ecosystem/certification-center")
@role_required(*HEALTHCARE_ECOSYSTEM_ROLES)
def healthcare_ecosystem_certification_center():
    return render_hub_page("Certification Center", build_certification_center_body())
@healthcare_ecosystem_web_bp.route("/healthcare-ecosystem/release-manager")
@role_required(*HEALTHCARE_ECOSYSTEM_ROLES)
def healthcare_ecosystem_release_manager():
    return render_hub_page("Release Manager", build_release_manager_body())
@healthcare_ecosystem_web_bp.route("/healthcare-ecosystem/license-manager")
@role_required(*HEALTHCARE_ECOSYSTEM_ROLES)
def healthcare_ecosystem_license_manager():
    return render_hub_page("License Manager", build_license_manager_body())
@healthcare_ecosystem_web_bp.route("/healthcare-ecosystem/commercial-readiness")
@role_required(*HEALTHCARE_ECOSYSTEM_ROLES)
def healthcare_ecosystem_commercial_readiness():
    return render_hub_page("Commercial Readiness", build_commercial_readiness_body())
@healthcare_ecosystem_web_bp.route("/healthcare-ecosystem/support-center")
@role_required(*HEALTHCARE_ECOSYSTEM_ROLES)
def healthcare_ecosystem_support_center():
    return render_hub_page("Support Center", build_support_center_body())
@healthcare_ecosystem_web_bp.route("/healthcare-ecosystem/knowledge-base")
@role_required(*HEALTHCARE_ECOSYSTEM_ROLES)
def healthcare_ecosystem_knowledge_base():
    return render_hub_page("Knowledge Base", build_knowledge_base_body())

