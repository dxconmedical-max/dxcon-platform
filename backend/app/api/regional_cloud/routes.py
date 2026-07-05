"""Regional Cloud Platform API routes — Phase 9."""

from __future__ import annotations

from flask import Blueprint

from app.services.regional_cloud_service import (
    dashboard_payload,
    regional_deployment,
    localization,
    internationalization,
    language_packs,
    currency_engine,
    tax_engine,
    timezone_engine,
    holiday_engine,
    regional_compliance,
    hipaa_compliance,
    gdpr_compliance,
    pdpa_compliance,
    iso27001_preparation,
    soc2_preparation,
    geo_replication,
    cross_region_federation,
    regional_marketplace,
    regional_partner_portal,
    cloud_abstraction_layer,
    aws_provider,
    azure_provider,
    google_cloud_provider,
    render_provider,
    on_premise_provider,
    multi_region_backup,
    disaster_recovery,
    regional_monitoring,
    regional_analytics,
    regional_cloud_readiness_report,
)

regional_cloud_bp = Blueprint("regional_cloud_api", __name__, url_prefix="/api/v1/regional-cloud")

@regional_cloud_bp.route("/dashboard", methods=["GET"])
def regional_cloud_dashboard_api():
    return dashboard_payload()

@regional_cloud_bp.route("/regional-deployment", methods=["GET"])
def regional_cloud_regional_deployment_api():
    return regional_deployment()

@regional_cloud_bp.route("/localization", methods=["GET"])
def regional_cloud_localization_api():
    return localization()

@regional_cloud_bp.route("/internationalization", methods=["GET"])
def regional_cloud_internationalization_api():
    return internationalization()

@regional_cloud_bp.route("/language-packs", methods=["GET"])
def regional_cloud_language_packs_api():
    return language_packs()

@regional_cloud_bp.route("/currency-engine", methods=["GET"])
def regional_cloud_currency_engine_api():
    return currency_engine()

@regional_cloud_bp.route("/tax-engine", methods=["GET"])
def regional_cloud_tax_engine_api():
    return tax_engine()

@regional_cloud_bp.route("/timezone-engine", methods=["GET"])
def regional_cloud_timezone_engine_api():
    return timezone_engine()

@regional_cloud_bp.route("/holiday-engine", methods=["GET"])
def regional_cloud_holiday_engine_api():
    return holiday_engine()

@regional_cloud_bp.route("/regional-compliance", methods=["GET"])
def regional_cloud_regional_compliance_api():
    return regional_compliance()

@regional_cloud_bp.route("/hipaa", methods=["GET"])
def regional_cloud_hipaa_compliance_api():
    return hipaa_compliance()

@regional_cloud_bp.route("/gdpr", methods=["GET"])
def regional_cloud_gdpr_compliance_api():
    return gdpr_compliance()

@regional_cloud_bp.route("/pdpa", methods=["GET"])
def regional_cloud_pdpa_compliance_api():
    return pdpa_compliance()

@regional_cloud_bp.route("/iso27001", methods=["GET"])
def regional_cloud_iso27001_preparation_api():
    return iso27001_preparation()

@regional_cloud_bp.route("/soc2", methods=["GET"])
def regional_cloud_soc2_preparation_api():
    return soc2_preparation()

@regional_cloud_bp.route("/geo-replication", methods=["GET"])
def regional_cloud_geo_replication_api():
    return geo_replication()

@regional_cloud_bp.route("/cross-region-federation", methods=["GET"])
def regional_cloud_cross_region_federation_api():
    return cross_region_federation()

@regional_cloud_bp.route("/regional-marketplace", methods=["GET"])
def regional_cloud_regional_marketplace_api():
    return regional_marketplace()

@regional_cloud_bp.route("/regional-partner-portal", methods=["GET"])
def regional_cloud_regional_partner_portal_api():
    return regional_partner_portal()

@regional_cloud_bp.route("/cloud-abstraction", methods=["GET"])
def regional_cloud_cloud_abstraction_layer_api():
    return cloud_abstraction_layer()

@regional_cloud_bp.route("/aws", methods=["GET"])
def regional_cloud_aws_provider_api():
    return aws_provider()

@regional_cloud_bp.route("/azure", methods=["GET"])
def regional_cloud_azure_provider_api():
    return azure_provider()

@regional_cloud_bp.route("/google-cloud", methods=["GET"])
def regional_cloud_google_cloud_provider_api():
    return google_cloud_provider()

@regional_cloud_bp.route("/render", methods=["GET"])
def regional_cloud_render_provider_api():
    return render_provider()

@regional_cloud_bp.route("/on-premise", methods=["GET"])
def regional_cloud_on_premise_provider_api():
    return on_premise_provider()

@regional_cloud_bp.route("/multi-region-backup", methods=["GET"])
def regional_cloud_multi_region_backup_api():
    return multi_region_backup()

@regional_cloud_bp.route("/disaster-recovery", methods=["GET"])
def regional_cloud_disaster_recovery_api():
    return disaster_recovery()

@regional_cloud_bp.route("/regional-monitoring", methods=["GET"])
def regional_cloud_regional_monitoring_api():
    return regional_monitoring()

@regional_cloud_bp.route("/regional-analytics", methods=["GET"])
def regional_cloud_regional_analytics_api():
    return regional_analytics()

@regional_cloud_bp.route("/readiness", methods=["GET"])
def regional_cloud_readiness_api():
    return regional_cloud_readiness_report()
