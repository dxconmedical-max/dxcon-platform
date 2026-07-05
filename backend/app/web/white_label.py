"""White Label web routes — Phase 7.9."""

from __future__ import annotations

from flask import Blueprint

from app.services.white_label_service import WHITE_LABEL_ROLES
from app.utils.auth import role_required
from app.web.white_label_lib import (
    build_dashboard_body,
    build_brand_theme_body,
    build_brand_logo_body,
    build_email_template_body,
    build_sms_template_body,
    build_tenant_domain_body,
    build_tenant_branding_body,
    build_tenant_config_body,
    render_hub_page,
)

white_label_web_bp = Blueprint("white_label_web", __name__)

@white_label_web_bp.route("/white-label")
@role_required(*WHITE_LABEL_ROLES)
def white_label_dashboard():
    return render_hub_page("White Label", build_dashboard_body())
@white_label_web_bp.route("/white-label/theme")
@role_required(*WHITE_LABEL_ROLES)
def white_label_brand_theme():
    return render_hub_page("Brand Theme", build_brand_theme_body())
@white_label_web_bp.route("/white-label/logo")
@role_required(*WHITE_LABEL_ROLES)
def white_label_brand_logo():
    return render_hub_page("Logo", build_brand_logo_body())
@white_label_web_bp.route("/white-label/email")
@role_required(*WHITE_LABEL_ROLES)
def white_label_email_template():
    return render_hub_page("Email Template", build_email_template_body())
@white_label_web_bp.route("/white-label/sms")
@role_required(*WHITE_LABEL_ROLES)
def white_label_sms_template():
    return render_hub_page("SMS Template", build_sms_template_body())
@white_label_web_bp.route("/white-label/domain")
@role_required(*WHITE_LABEL_ROLES)
def white_label_tenant_domain():
    return render_hub_page("Tenant Domain", build_tenant_domain_body())
@white_label_web_bp.route("/white-label/branding")
@role_required(*WHITE_LABEL_ROLES)
def white_label_tenant_branding():
    return render_hub_page("Tenant Branding", build_tenant_branding_body())
@white_label_web_bp.route("/white-label/config")
@role_required(*WHITE_LABEL_ROLES)
def white_label_tenant_config():
    return render_hub_page("Tenant Config", build_tenant_config_body())

