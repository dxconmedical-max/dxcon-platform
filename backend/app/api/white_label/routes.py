"""White Label API routes — Phase 7.9."""

from __future__ import annotations

from flask import Blueprint

from app.services.white_label_service import (
    dashboard_payload,
    brand_theme,
    brand_logo,
    email_template,
    sms_template,
    tenant_domain,
    tenant_branding,
    tenant_config,
    white_label_readiness_report,
)

white_label_bp = Blueprint("white_label_api", __name__, url_prefix="/api/v1/white-label")

@white_label_bp.route("/dashboard", methods=["GET"])
def white_label_dashboard_api():
    return dashboard_payload()

@white_label_bp.route("/theme", methods=["GET"])
def white_label_brand_theme_api():
    return brand_theme()

@white_label_bp.route("/logo", methods=["GET"])
def white_label_brand_logo_api():
    return brand_logo()

@white_label_bp.route("/email", methods=["GET"])
def white_label_email_template_api():
    return email_template()

@white_label_bp.route("/sms", methods=["GET"])
def white_label_sms_template_api():
    return sms_template()

@white_label_bp.route("/domain", methods=["GET"])
def white_label_tenant_domain_api():
    return tenant_domain()

@white_label_bp.route("/branding", methods=["GET"])
def white_label_tenant_branding_api():
    return tenant_branding()

@white_label_bp.route("/config", methods=["GET"])
def white_label_tenant_config_api():
    return tenant_config()

@white_label_bp.route("/readiness", methods=["GET"])
def white_label_readiness_api():
    return white_label_readiness_report()
