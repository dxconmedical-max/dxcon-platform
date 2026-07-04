"""Security & Compliance web routes — Phase 5 Sprint 5.1."""

from __future__ import annotations

from flask import Blueprint

from app.services.security_compliance_service import SECURITY_ROLES
from app.utils.auth import role_required
from app.web.security_compliance_lib import (
    build_api_keys_body,
    build_audit_body,
    build_compliance_body,
    build_dashboard_body,
    build_failed_logins_body,
    build_ip_whitelist_body,
    build_jwt_body,
    build_phi_access_body,
    build_rate_limits_body,
    build_rbac_body,
    build_secrets_body,
    build_timeline_body,
    render_security_page,
)

security_compliance_web_bp = Blueprint("security_compliance_web", __name__)


@security_compliance_web_bp.route("/security-compliance")
@role_required(*SECURITY_ROLES)
def security_compliance_dashboard():
    return render_security_page("Security & Compliance", build_dashboard_body())


@security_compliance_web_bp.route("/security-compliance/secrets")
@role_required(*SECURITY_ROLES)
def security_compliance_secrets():
    return render_security_page("Secret Management Audit", build_secrets_body())


@security_compliance_web_bp.route("/security-compliance/api-keys")
@role_required(*SECURITY_ROLES)
def security_compliance_api_keys():
    return render_security_page("API Key Rotation", build_api_keys_body())


@security_compliance_web_bp.route("/security-compliance/jwt")
@role_required(*SECURITY_ROLES)
def security_compliance_jwt():
    return render_security_page("JWT Audit", build_jwt_body())


@security_compliance_web_bp.route("/security-compliance/rbac")
@role_required(*SECURITY_ROLES)
def security_compliance_rbac():
    return render_security_page("RBAC Permission Matrix", build_rbac_body())


@security_compliance_web_bp.route("/security-compliance/audit")
@role_required(*SECURITY_ROLES)
def security_compliance_audit():
    return render_security_page("Audit Log Viewer", build_audit_body())


@security_compliance_web_bp.route("/security-compliance/timeline")
@role_required(*SECURITY_ROLES)
def security_compliance_timeline():
    return render_security_page("Security Event Timeline", build_timeline_body())


@security_compliance_web_bp.route("/security-compliance/failed-logins")
@role_required(*SECURITY_ROLES)
def security_compliance_failed_logins():
    return render_security_page("Failed Login Analytics", build_failed_logins_body())


@security_compliance_web_bp.route("/security-compliance/ip-whitelist")
@role_required(*SECURITY_ROLES)
def security_compliance_ip_whitelist():
    return render_security_page("IP Whitelist Framework", build_ip_whitelist_body())


@security_compliance_web_bp.route("/security-compliance/rate-limits")
@role_required(*SECURITY_ROLES)
def security_compliance_rate_limits():
    return render_security_page("Rate Limit Dashboard", build_rate_limits_body())


@security_compliance_web_bp.route("/security-compliance/phi-access")
@role_required(*SECURITY_ROLES)
def security_compliance_phi_access():
    return render_security_page("PHI Access Audit", build_phi_access_body())


@security_compliance_web_bp.route("/security-compliance/compliance")
@role_required(*SECURITY_ROLES)
def security_compliance_compliance():
    return render_security_page("Compliance Report", build_compliance_body())
