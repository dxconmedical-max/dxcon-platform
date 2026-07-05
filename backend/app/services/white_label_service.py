"""White Label platform business logic for Phase 7.9."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from app.models.enterprise_platform import EnterpriseTenant, TenantOrganizationSetting
from app.services.multi_tenant_foundation_service import organization_settings
from app.services.reporting_service import _safe

WHITE_LABEL_ROLES = ("SUPER_ADMIN", "ADMIN")

FEATURES = (
    "Brand Theme",
    "Logo",
    "Email Template",
    "SMS Template",
    "Tenant Domain",
    "Tenant Branding",
    "Tenant Config",
)

DEFAULT_BRAND = {
    "primary_color": "#0a4b5c",
    "secondary_color": "#0d6efd",
    "accent_color": "#15803d",
    "logo_url": "/static/branding/dxcon-logo.svg",
    "email_header": "DxCon Diagnostics",
    "sms_sender": "DxCon",
    "domain_pattern": "{tenant_code}.dxcon.app",
}


def ensure_white_label() -> dict[str, Any]:
    tenant = EnterpriseTenant.query.first()
    if not tenant:
        return {"ready": True}
    for key, value, category in (
        ("primary_color", DEFAULT_BRAND["primary_color"], "BRAND"),
        ("logo_url", DEFAULT_BRAND["logo_url"], "BRAND"),
        ("email_header", DEFAULT_BRAND["email_header"], "EMAIL"),
        ("sms_sender", DEFAULT_BRAND["sms_sender"], "SMS"),
    ):
        if TenantOrganizationSetting.query.filter_by(tenant_id=tenant.id, setting_key=key).first():
            continue
        from app.extensions.db import db

        db.session.add(
            TenantOrganizationSetting(
                tenant_id=tenant.id,
                setting_key=key,
                setting_value=value,
                category=category,
            )
        )
    from app.extensions.db import db

    db.session.commit()
    return {"ready": True}


def _brand_settings() -> list[dict]:
    data = organization_settings()
    return data.get("settings", [])


def brand_theme() -> dict[str, Any]:
    ensure_white_label()
    return {"report": "brand_theme", "theme": DEFAULT_BRAND, "settings": _brand_settings()}


def brand_logo() -> dict[str, Any]:
    ensure_white_label()
    return {"report": "brand_logo", "logo_url": DEFAULT_BRAND["logo_url"], "formats": ["svg", "png"]}


def email_template() -> dict[str, Any]:
    return {"report": "email_template", "header": DEFAULT_BRAND["email_header"], "layout": "branded_html"}


def sms_template() -> dict[str, Any]:
    return {"report": "sms_template", "sender": DEFAULT_BRAND["sms_sender"], "max_length": 160}


def tenant_domain() -> dict[str, Any]:
    tenants = _safe(lambda: EnterpriseTenant.query.count(), 0)
    return {"report": "tenant_domain", "pattern": DEFAULT_BRAND["domain_pattern"], "tenants": tenants}


def tenant_branding() -> dict[str, Any]:
    ensure_white_label()
    return {"report": "tenant_branding", "brand": DEFAULT_BRAND, "multi_tenant": True}


def tenant_config() -> dict[str, Any]:
    ensure_white_label()
    return {"report": "tenant_config", "settings": _brand_settings()}


def dashboard_payload() -> dict[str, Any]:
    ensure_white_label()
    return {
        "platform": "White Label",
        "phase": "7.9",
        "sprint": "White Label",
        "status": "OK",
        "generated_at": datetime.utcnow().isoformat(),
        "summary": {"brand_keys": len(DEFAULT_BRAND), "settings": len(_brand_settings())},
        "features": list(FEATURES),
    }


def white_label_readiness_report() -> dict[str, Any]:
    d = dashboard_payload()
    return {
        "generated_at": datetime.utcnow().isoformat(),
        "phase": "7.9",
        "platform": d["platform"],
        "status": d["status"],
        "summary": d["summary"],
        "features": list(FEATURES),
        "sections": {
            "brand_theme": brand_theme(),
            "brand_logo": brand_logo(),
            "email_template": email_template(),
            "sms_template": sms_template(),
            "tenant_domain": tenant_domain(),
            "tenant_branding": tenant_branding(),
            "tenant_config": tenant_config(),
        },
        "legacy_routes": ["/api/v1/multi-tenant/settings"],
        "guide": "docs/WHITE_LABEL_GUIDE.md",
    }
