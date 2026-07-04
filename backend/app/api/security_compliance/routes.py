"""Security & Compliance API routes — Phase 5 Sprint 5.1."""

from __future__ import annotations

from flask import Blueprint, request

from app.services.security_compliance_service import (
    SecurityComplianceError,
    api_key_rotation_status,
    audit_log_viewer,
    compliance_report,
    dashboard_payload,
    failed_login_analytics,
    ip_whitelist_framework,
    jwt_audit,
    phi_access_audit,
    rate_limit_dashboard,
    rbac_permission_matrix,
    rotate_api_key,
    secret_management_audit,
    security_event_timeline,
    security_readiness_report,
)

security_compliance_bp = Blueprint(
    "security_compliance_api",
    __name__,
    url_prefix="/api/v1/security-compliance",
)


@security_compliance_bp.route("/dashboard", methods=["GET"])
def security_compliance_dashboard_api():
    return dashboard_payload()


@security_compliance_bp.route("/secrets", methods=["GET"])
def security_compliance_secrets_api():
    return secret_management_audit()


@security_compliance_bp.route("/api-keys", methods=["GET"])
def security_compliance_api_keys_api():
    return api_key_rotation_status()


@security_compliance_bp.route("/api-keys/<key_id>/rotate", methods=["POST"])
def security_compliance_rotate_api_key_api(key_id: str):
    try:
        return rotate_api_key(key_id)
    except SecurityComplianceError as exc:
        return {"error": exc.message}, exc.status_code


@security_compliance_bp.route("/jwt", methods=["GET"])
def security_compliance_jwt_api():
    limit = int(request.args.get("limit") or 50)
    return jwt_audit(limit=limit)


@security_compliance_bp.route("/rbac", methods=["GET"])
def security_compliance_rbac_api():
    return rbac_permission_matrix()


@security_compliance_bp.route("/audit", methods=["GET"])
def security_compliance_audit_api():
    limit = int(request.args.get("limit") or 100)
    return audit_log_viewer(limit=limit)


@security_compliance_bp.route("/timeline", methods=["GET"])
def security_compliance_timeline_api():
    limit = int(request.args.get("limit") or 100)
    return security_event_timeline(limit=limit)


@security_compliance_bp.route("/failed-logins", methods=["GET"])
def security_compliance_failed_logins_api():
    limit = int(request.args.get("limit") or 100)
    return failed_login_analytics(limit=limit)


@security_compliance_bp.route("/ip-whitelist", methods=["GET"])
def security_compliance_ip_whitelist_api():
    return ip_whitelist_framework()


@security_compliance_bp.route("/rate-limits", methods=["GET"])
def security_compliance_rate_limits_api():
    return rate_limit_dashboard()


@security_compliance_bp.route("/phi-access", methods=["GET"])
def security_compliance_phi_access_api():
    limit = int(request.args.get("limit") or 100)
    return phi_access_audit(limit=limit)


@security_compliance_bp.route("/compliance", methods=["GET"])
def security_compliance_compliance_api():
    return compliance_report()


@security_compliance_bp.route("/readiness", methods=["GET"])
def security_compliance_readiness_api():
    return security_readiness_report()
