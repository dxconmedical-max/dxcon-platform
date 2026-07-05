"""Regional Cloud Platform business logic for Phase 9."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from flask import current_app

from app.infrastructure.infrastructure_services import InfrastructureHealthService, InfrastructureReadinessService
from app.services.backup_recovery_service import backup_scheduler, disaster_recovery_runbook
from app.services.enterprise_analytics_service import dashboard_payload as analytics_dashboard
from app.services.federation_platform_service import cross_organization_exchange, regional_hub
from app.services.marketplace_platform_service import marketplace_overview
from app.services.monitoring_center_service import application_health, dashboard_payload as monitoring_dashboard
from app.services.multi_tenant_foundation_service import organization_settings
from app.services.production_deployment_service import DEPLOYMENT_ASSETS, docker_production_profile
from app.services.security_compliance_service import compliance_report
from app.services.white_label_service import brand_theme

REGIONAL_CLOUD_ROLES = ("SUPER_ADMIN", "ADMIN")

ROOT = Path(__file__).resolve().parents[2]
REPO = ROOT.parent

GOVERNANCE = {
    "backward_compatible": True,
    "destructive_migrations": False,
    "postgresql_only": True,
    "multi_region_ready": True,
    "data_residency_aware": True,
}

FEATURES = (
    "Regional Deployment",
    "Localization",
    "Internationalization",
    "Language Packs",
    "Currency Engine",
    "Tax Engine",
    "Timezone Engine",
    "Holiday Engine",
    "Regional Compliance",
    "HIPAA",
    "GDPR",
    "PDPA",
    "ISO27001",
    "SOC2 Preparation",
    "Geo Replication",
    "Cross-region Federation",
    "Regional Marketplace",
    "Regional Partner Portal",
    "Cloud Abstraction Layer",
    "AWS",
    "Azure",
    "Google Cloud",
    "Render",
    "On-premise",
    "Multi-region Backup",
    "Disaster Recovery",
    "Regional Monitoring",
    "Regional Analytics",
)

SUPPORTED_REGIONS = (
    {"code": "VN", "name": "Vietnam", "timezone": "Asia/Ho_Chi_Minh", "currency": "VND", "locale": "vi-VN"},
    {"code": "US", "name": "United States", "timezone": "America/New_York", "currency": "USD", "locale": "en-US"},
    {"code": "EU", "name": "European Union", "timezone": "Europe/Berlin", "currency": "EUR", "locale": "en-GB"},
    {"code": "SG", "name": "Singapore", "timezone": "Asia/Singapore", "currency": "SGD", "locale": "en-SG"},
)

LANGUAGE_PACKS = (
    {"code": "vi-VN", "name": "Tiếng Việt", "status": "READY"},
    {"code": "en-US", "name": "English (US)", "status": "READY"},
    {"code": "en-GB", "name": "English (UK)", "status": "READY"},
    {"code": "ja-JP", "name": "日本語", "status": "SCAFFOLD"},
)

CURRENCY_RATES = (
    {"base": "USD", "VND": 24500, "EUR": 0.92, "SGD": 1.34},
)

TAX_PROFILES = (
    {"region": "VN", "vat_rate": 0.08, "healthcare_exempt": True},
    {"region": "US", "sales_tax": "state_varies", "healthcare_exempt": False},
    {"region": "EU", "vat_rate": "country_varies", "healthcare_exempt": True},
)

HOLIDAY_CALENDARS = (
    {"region": "VN", "calendar": "vietnam_public_holidays", "engine": "timezone_engine"},
    {"region": "US", "calendar": "federal_holidays", "engine": "timezone_engine"},
)

COMPLIANCE_FRAMEWORKS = {
    "HIPAA": {"scope": "US healthcare PHI", "controls": ["access_audit", "encryption", "baa_required"], "status": "PREPARED"},
    "GDPR": {"scope": "EU personal data", "controls": ["consent", "erasure", "dpia"], "status": "PREPARED"},
    "PDPA": {"scope": "Singapore/ASEAN personal data", "controls": ["consent", "cross_border_transfer"], "status": "PREPARED"},
    "ISO27001": {"scope": "ISMS", "controls": ["risk_assessment", "asset_inventory", "incident_response"], "status": "PREPARATION"},
    "SOC2": {"scope": "Trust services", "controls": ["security", "availability", "confidentiality"], "status": "PREPARATION"},
}

CLOUD_PROVIDERS = (
    {"id": "aws", "name": "AWS", "services": ["RDS", "S3", "EKS", "CloudWatch"], "status": "READY"},
    {"id": "azure", "name": "Azure", "services": ["PostgreSQL", "Blob", "AKS", "Monitor"], "status": "READY"},
    {"id": "gcp", "name": "Google Cloud", "services": ["Cloud SQL", "GCS", "GKE", "Operations"], "status": "READY"},
    {"id": "render", "name": "Render", "services": ["Web Service", "PostgreSQL", "Redis"], "status": "READY"},
    {"id": "on_prem", "name": "On-premise", "services": ["Docker", "Kubernetes", "Bare metal"], "status": "READY"},
)


def ensure_regional_cloud() -> dict[str, Any]:
    return {"ready": True, **GOVERNANCE}


def regional_deployment() -> dict[str, Any]:
    ensure_regional_cloud()
    docker = docker_production_profile()
    infra = InfrastructureReadinessService.readiness(current_app)
    return {
        "report": "regional_deployment",
        "regions": list(SUPPORTED_REGIONS),
        "docker_profile": docker.get("checks", {}),
        "infrastructure_ready": infra.get("ready"),
        "legacy_route": "/production-deployment",
        "assets": {k: v.exists() for k, v in DEPLOYMENT_ASSETS.items()},
    }


def localization() -> dict[str, Any]:
    ensure_regional_cloud()
    brand = brand_theme()
    settings = organization_settings()
    return {
        "report": "localization",
        "brand": brand.get("theme"),
        "tenant_settings": settings.get("count", 0),
        "default_locale": "vi-VN",
        "legacy_route": "/white-label",
    }


def internationalization() -> dict[str, Any]:
    ensure_regional_cloud()
    return {
        "report": "internationalization",
        "supported_locales": [pack["code"] for pack in LANGUAGE_PACKS],
        "fallback_locale": "en-US",
        "rtl_support": False,
    }


def language_packs() -> dict[str, Any]:
    ensure_regional_cloud()
    return {"report": "language_packs", "packs": list(LANGUAGE_PACKS)}


def currency_engine() -> dict[str, Any]:
    ensure_regional_cloud()
    return {
        "report": "currency_engine",
        "base_currency": "USD",
        "supported_currencies": ["USD", "VND", "EUR", "SGD"],
        "sample_rates": list(CURRENCY_RATES),
        "status": "SCAFFOLD",
    }


def tax_engine() -> dict[str, Any]:
    ensure_regional_cloud()
    return {"report": "tax_engine", "profiles": list(TAX_PROFILES), "status": "SCAFFOLD"}


def timezone_engine() -> dict[str, Any]:
    ensure_regional_cloud()
    settings = organization_settings()
    tz_setting = next(
        (s for s in settings.get("settings", []) if s.get("setting_key") == "timezone"),
        {"setting_value": "Asia/Ho_Chi_Minh"},
    )
    return {
        "report": "timezone_engine",
        "default_timezone": tz_setting.get("setting_value"),
        "regions": [{"code": r["code"], "timezone": r["timezone"]} for r in SUPPORTED_REGIONS],
    }


def holiday_engine() -> dict[str, Any]:
    ensure_regional_cloud()
    return {"report": "holiday_engine", "calendars": list(HOLIDAY_CALENDARS), "status": "SCAFFOLD"}


def regional_compliance() -> dict[str, Any]:
    ensure_regional_cloud()
    report = compliance_report()
    return {
        "report": "regional_compliance",
        "frameworks": list(COMPLIANCE_FRAMEWORKS.keys()),
        "security_compliance": report.get("report"),
        "legacy_route": "/security-compliance",
    }


def _framework(name: str) -> dict[str, Any]:
    ensure_regional_cloud()
    framework = COMPLIANCE_FRAMEWORKS[name]
    return {"report": name.lower(), "framework": name, **framework}


def hipaa_compliance() -> dict[str, Any]:
    return _framework("HIPAA")


def gdpr_compliance() -> dict[str, Any]:
    return _framework("GDPR")


def pdpa_compliance() -> dict[str, Any]:
    return _framework("PDPA")


def iso27001_preparation() -> dict[str, Any]:
    return _framework("ISO27001")


def soc2_preparation() -> dict[str, Any]:
    return _framework("SOC2")


def geo_replication() -> dict[str, Any]:
    ensure_regional_cloud()
    return {
        "report": "geo_replication",
        "status": "SCAFFOLD",
        "primary_region": "VN",
        "replica_regions": ["SG", "US"],
        "strategy": "async_read_replica",
        "postgres_compatible": True,
    }


def cross_region_federation() -> dict[str, Any]:
    ensure_regional_cloud()
    regional = regional_hub()
    exchange = cross_organization_exchange()
    return {
        "report": "cross_region_federation",
        "regional_hub": regional,
        "exchange": exchange,
        "legacy_route": "/federation-platform",
    }


def regional_marketplace() -> dict[str, Any]:
    ensure_regional_cloud()
    marketplace = marketplace_overview()
    return {
        "report": "regional_marketplace",
        "marketplace": marketplace,
        "regions": [r["code"] for r in SUPPORTED_REGIONS],
        "legacy_route": "/marketplace-platform",
    }


def regional_partner_portal() -> dict[str, Any]:
    ensure_regional_cloud()
    marketplace = marketplace_overview()
    return {
        "report": "regional_partner_portal",
        "active_partners": marketplace.get("active_partners", 0),
        "portal_routes": ["/developer", "/marketplace-platform"],
        "status": "READY",
    }


def cloud_abstraction_layer() -> dict[str, Any]:
    ensure_regional_cloud()
    health = InfrastructureHealthService.status(current_app)
    return {
        "report": "cloud_abstraction_layer",
        "providers": [p["id"] for p in CLOUD_PROVIDERS],
        "runtime_profile": health.get("runtime_profile"),
        "deployment_score": health.get("deployment_score"),
    }


def _cloud_provider(provider_id: str) -> dict[str, Any]:
    ensure_regional_cloud()
    provider = next(p for p in CLOUD_PROVIDERS if p["id"] == provider_id)
    return {"report": f"{provider_id}_provider", **provider}


def aws_provider() -> dict[str, Any]:
    return _cloud_provider("aws")


def azure_provider() -> dict[str, Any]:
    return _cloud_provider("azure")


def google_cloud_provider() -> dict[str, Any]:
    return _cloud_provider("gcp")


def render_provider() -> dict[str, Any]:
    return _cloud_provider("render")


def on_premise_provider() -> dict[str, Any]:
    return _cloud_provider("on_prem")


def multi_region_backup() -> dict[str, Any]:
    ensure_regional_cloud()
    scheduler = backup_scheduler()
    return {
        "report": "multi_region_backup",
        "scheduler": scheduler,
        "regions": ["primary", "dr_secondary"],
        "legacy_route": "/backup-recovery",
    }


def disaster_recovery() -> dict[str, Any]:
    ensure_regional_cloud()
    runbook = disaster_recovery_runbook()
    return {
        "report": "disaster_recovery",
        "runbook": runbook,
        "rto_target_minutes": 60,
        "rpo_target_minutes": 15,
        "legacy_route": "/backup-recovery",
    }


def regional_monitoring() -> dict[str, Any]:
    ensure_regional_cloud()
    health = application_health()
    monitoring = monitoring_dashboard()
    return {
        "report": "regional_monitoring",
        "application_health": health.get("status"),
        "monitoring_summary": monitoring.get("summary", {}),
        "legacy_route": "/monitoring-center",
    }


def regional_analytics() -> dict[str, Any]:
    ensure_regional_cloud()
    analytics = analytics_dashboard()
    return {
        "report": "regional_analytics",
        "analytics_summary": analytics.get("summary", {}),
        "regions": [r["code"] for r in SUPPORTED_REGIONS],
        "legacy_route": "/enterprise-analytics",
    }


def dashboard_payload() -> dict[str, Any]:
    ensure_regional_cloud()
    return {
        "platform": "Regional Cloud Platform",
        "phase": "9",
        "sprint": "Regional Cloud Platform",
        "status": "OK",
        "governance": GOVERNANCE,
        "generated_at": datetime.utcnow().isoformat(),
        "summary": {
            "modules": len(FEATURES),
            "regions": len(SUPPORTED_REGIONS),
            "cloud_providers": len(CLOUD_PROVIDERS),
            "compliance_frameworks": len(COMPLIANCE_FRAMEWORKS),
            "language_packs": len(LANGUAGE_PACKS),
            "scaffold_modules": 4,
        },
        "features": list(FEATURES),
    }


def regional_cloud_readiness_report() -> dict[str, Any]:
    d = dashboard_payload()
    return {
        "generated_at": datetime.utcnow().isoformat(),
        "phase": "9",
        "platform": d["platform"],
        "status": d["status"],
        "governance": GOVERNANCE,
        "summary": d["summary"],
        "features": list(FEATURES),
        "regions": list(SUPPORTED_REGIONS),
        "sections": {
            "regional_deployment": regional_deployment(),
            "regional_compliance": regional_compliance(),
            "cloud_abstraction_layer": cloud_abstraction_layer(),
            "multi_region_backup": multi_region_backup(),
            "disaster_recovery": disaster_recovery(),
            "cross_region_federation": cross_region_federation(),
        },
        "architecture_docs": [
            "docs/architecture/REGIONAL_ARCHITECTURE.md",
            "docs/architecture/DEPLOYMENT_ARCHITECTURE.md",
            "docs/COMPLIANCE_GUIDE.md",
        ],
        "legacy_hubs": [
            "/production-deployment",
            "/federation-platform",
            "/marketplace-platform",
            "/backup-recovery",
            "/security-compliance",
        ],
    }


def regional_cloud_deployment_report() -> dict[str, Any]:
    deployment = regional_deployment()
    cloud = cloud_abstraction_layer()
    backup = multi_region_backup()
    dr = disaster_recovery()
    return {
        "generated_at": datetime.utcnow().isoformat(),
        "phase": "9",
        "platform": "Regional Cloud Platform",
        "governance": GOVERNANCE,
        "deployment": deployment,
        "cloud_abstraction": cloud,
        "backup": backup,
        "disaster_recovery": dr,
        "providers": list(CLOUD_PROVIDERS),
        "regions": list(SUPPORTED_REGIONS),
        "readiness_score": 100 if deployment.get("infrastructure_ready") else 85,
    }
