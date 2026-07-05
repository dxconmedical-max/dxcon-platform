"""Regional Cloud Platform web routes — Phase 9."""

from __future__ import annotations

from flask import Blueprint

from app.services.regional_cloud_service import REGIONAL_CLOUD_ROLES
from app.utils.auth import role_required
from app.web.regional_cloud_lib import (
    build_dashboard_body,
    build_regional_deployment_body,
    build_localization_body,
    build_internationalization_body,
    build_language_packs_body,
    build_currency_engine_body,
    build_tax_engine_body,
    build_timezone_engine_body,
    build_holiday_engine_body,
    build_regional_compliance_body,
    build_hipaa_compliance_body,
    build_gdpr_compliance_body,
    build_pdpa_compliance_body,
    build_iso27001_preparation_body,
    build_soc2_preparation_body,
    build_geo_replication_body,
    build_cross_region_federation_body,
    build_regional_marketplace_body,
    build_regional_partner_portal_body,
    build_cloud_abstraction_layer_body,
    build_aws_provider_body,
    build_azure_provider_body,
    build_google_cloud_provider_body,
    build_render_provider_body,
    build_on_premise_provider_body,
    build_multi_region_backup_body,
    build_disaster_recovery_body,
    build_regional_monitoring_body,
    build_regional_analytics_body,
    render_hub_page,
)

regional_cloud_web_bp = Blueprint("regional_cloud_web", __name__)

@regional_cloud_web_bp.route("/regional-cloud")
@role_required(*REGIONAL_CLOUD_ROLES)
def regional_cloud_dashboard():
    return render_hub_page("Regional Cloud Platform", build_dashboard_body())
@regional_cloud_web_bp.route("/regional-cloud/regional-deployment")
@role_required(*REGIONAL_CLOUD_ROLES)
def regional_cloud_regional_deployment():
    return render_hub_page("Regional Deployment", build_regional_deployment_body())
@regional_cloud_web_bp.route("/regional-cloud/localization")
@role_required(*REGIONAL_CLOUD_ROLES)
def regional_cloud_localization():
    return render_hub_page("Localization", build_localization_body())
@regional_cloud_web_bp.route("/regional-cloud/internationalization")
@role_required(*REGIONAL_CLOUD_ROLES)
def regional_cloud_internationalization():
    return render_hub_page("Internationalization", build_internationalization_body())
@regional_cloud_web_bp.route("/regional-cloud/language-packs")
@role_required(*REGIONAL_CLOUD_ROLES)
def regional_cloud_language_packs():
    return render_hub_page("Language Packs", build_language_packs_body())
@regional_cloud_web_bp.route("/regional-cloud/currency-engine")
@role_required(*REGIONAL_CLOUD_ROLES)
def regional_cloud_currency_engine():
    return render_hub_page("Currency Engine", build_currency_engine_body())
@regional_cloud_web_bp.route("/regional-cloud/tax-engine")
@role_required(*REGIONAL_CLOUD_ROLES)
def regional_cloud_tax_engine():
    return render_hub_page("Tax Engine", build_tax_engine_body())
@regional_cloud_web_bp.route("/regional-cloud/timezone-engine")
@role_required(*REGIONAL_CLOUD_ROLES)
def regional_cloud_timezone_engine():
    return render_hub_page("Timezone Engine", build_timezone_engine_body())
@regional_cloud_web_bp.route("/regional-cloud/holiday-engine")
@role_required(*REGIONAL_CLOUD_ROLES)
def regional_cloud_holiday_engine():
    return render_hub_page("Holiday Engine", build_holiday_engine_body())
@regional_cloud_web_bp.route("/regional-cloud/regional-compliance")
@role_required(*REGIONAL_CLOUD_ROLES)
def regional_cloud_regional_compliance():
    return render_hub_page("Regional Compliance", build_regional_compliance_body())
@regional_cloud_web_bp.route("/regional-cloud/hipaa")
@role_required(*REGIONAL_CLOUD_ROLES)
def regional_cloud_hipaa_compliance():
    return render_hub_page("HIPAA", build_hipaa_compliance_body())
@regional_cloud_web_bp.route("/regional-cloud/gdpr")
@role_required(*REGIONAL_CLOUD_ROLES)
def regional_cloud_gdpr_compliance():
    return render_hub_page("GDPR", build_gdpr_compliance_body())
@regional_cloud_web_bp.route("/regional-cloud/pdpa")
@role_required(*REGIONAL_CLOUD_ROLES)
def regional_cloud_pdpa_compliance():
    return render_hub_page("PDPA", build_pdpa_compliance_body())
@regional_cloud_web_bp.route("/regional-cloud/iso27001")
@role_required(*REGIONAL_CLOUD_ROLES)
def regional_cloud_iso27001_preparation():
    return render_hub_page("ISO27001", build_iso27001_preparation_body())
@regional_cloud_web_bp.route("/regional-cloud/soc2")
@role_required(*REGIONAL_CLOUD_ROLES)
def regional_cloud_soc2_preparation():
    return render_hub_page("SOC2 Preparation", build_soc2_preparation_body())
@regional_cloud_web_bp.route("/regional-cloud/geo-replication")
@role_required(*REGIONAL_CLOUD_ROLES)
def regional_cloud_geo_replication():
    return render_hub_page("Geo Replication", build_geo_replication_body())
@regional_cloud_web_bp.route("/regional-cloud/cross-region-federation")
@role_required(*REGIONAL_CLOUD_ROLES)
def regional_cloud_cross_region_federation():
    return render_hub_page("Cross-region Federation", build_cross_region_federation_body())
@regional_cloud_web_bp.route("/regional-cloud/regional-marketplace")
@role_required(*REGIONAL_CLOUD_ROLES)
def regional_cloud_regional_marketplace():
    return render_hub_page("Regional Marketplace", build_regional_marketplace_body())
@regional_cloud_web_bp.route("/regional-cloud/regional-partner-portal")
@role_required(*REGIONAL_CLOUD_ROLES)
def regional_cloud_regional_partner_portal():
    return render_hub_page("Regional Partner Portal", build_regional_partner_portal_body())
@regional_cloud_web_bp.route("/regional-cloud/cloud-abstraction")
@role_required(*REGIONAL_CLOUD_ROLES)
def regional_cloud_cloud_abstraction_layer():
    return render_hub_page("Cloud Abstraction Layer", build_cloud_abstraction_layer_body())
@regional_cloud_web_bp.route("/regional-cloud/aws")
@role_required(*REGIONAL_CLOUD_ROLES)
def regional_cloud_aws_provider():
    return render_hub_page("AWS", build_aws_provider_body())
@regional_cloud_web_bp.route("/regional-cloud/azure")
@role_required(*REGIONAL_CLOUD_ROLES)
def regional_cloud_azure_provider():
    return render_hub_page("Azure", build_azure_provider_body())
@regional_cloud_web_bp.route("/regional-cloud/google-cloud")
@role_required(*REGIONAL_CLOUD_ROLES)
def regional_cloud_google_cloud_provider():
    return render_hub_page("Google Cloud", build_google_cloud_provider_body())
@regional_cloud_web_bp.route("/regional-cloud/render")
@role_required(*REGIONAL_CLOUD_ROLES)
def regional_cloud_render_provider():
    return render_hub_page("Render", build_render_provider_body())
@regional_cloud_web_bp.route("/regional-cloud/on-premise")
@role_required(*REGIONAL_CLOUD_ROLES)
def regional_cloud_on_premise_provider():
    return render_hub_page("On-premise", build_on_premise_provider_body())
@regional_cloud_web_bp.route("/regional-cloud/multi-region-backup")
@role_required(*REGIONAL_CLOUD_ROLES)
def regional_cloud_multi_region_backup():
    return render_hub_page("Multi-region Backup", build_multi_region_backup_body())
@regional_cloud_web_bp.route("/regional-cloud/disaster-recovery")
@role_required(*REGIONAL_CLOUD_ROLES)
def regional_cloud_disaster_recovery():
    return render_hub_page("Disaster Recovery", build_disaster_recovery_body())
@regional_cloud_web_bp.route("/regional-cloud/regional-monitoring")
@role_required(*REGIONAL_CLOUD_ROLES)
def regional_cloud_regional_monitoring():
    return render_hub_page("Regional Monitoring", build_regional_monitoring_body())
@regional_cloud_web_bp.route("/regional-cloud/regional-analytics")
@role_required(*REGIONAL_CLOUD_ROLES)
def regional_cloud_regional_analytics():
    return render_hub_page("Regional Analytics", build_regional_analytics_body())

