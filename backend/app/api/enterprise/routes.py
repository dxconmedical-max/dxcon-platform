from flask import Blueprint, request

from app.services.enterprise_platform_service import (
    AdminEnterpriseService,
    AuditEnterpriseService,
    EnterpriseError,
    LicenseEnterpriseService,
    MonitoringEnterpriseService,
    OrganizationEnterpriseService,
    SecurityEnterpriseService,
    TenantEnterpriseService,
)


def _error(exc):
    return {"error": exc.message}, exc.status_code


enterprise_admin_bp = Blueprint("enterprise_admin", __name__, url_prefix="/api/v1/admin")
tenants_bp = Blueprint("enterprise_tenants", __name__, url_prefix="/api/v1/tenants")
licenses_bp = Blueprint("enterprise_licenses", __name__, url_prefix="/api/v1/licenses")
enterprise_security_bp = Blueprint("enterprise_security", __name__, url_prefix="/api/v1/security")
audit_bp = Blueprint("enterprise_audit", __name__, url_prefix="/api/v1/audit")


@enterprise_admin_bp.route("/overview", methods=["GET"])
def admin_overview():
    return AdminEnterpriseService.overview()


@enterprise_admin_bp.route("/settings", methods=["GET"])
def list_settings():
    return AdminEnterpriseService.list_settings()


@enterprise_admin_bp.route("/settings", methods=["POST"])
def upsert_setting():
    data = request.get_json(silent=True) or {}
    try:
        return AdminEnterpriseService.upsert_setting(data), 201
    except EnterpriseError as exc:
        return _error(exc)


@enterprise_admin_bp.route("/feature-flags", methods=["GET"])
def list_feature_flags():
    return AdminEnterpriseService.list_feature_flags(tenant_id=request.args.get("tenant_id"))


@enterprise_admin_bp.route("/feature-flags", methods=["POST"])
def upsert_feature_flag():
    data = request.get_json(silent=True) or {}
    return AdminEnterpriseService.upsert_feature_flag(data), 201


@enterprise_admin_bp.route("/usage", methods=["GET"])
def usage_statistics():
    return AdminEnterpriseService.usage_statistics(tenant_id=request.args.get("tenant_id"))


@enterprise_admin_bp.route("/health", methods=["GET"])
def admin_health():
    return MonitoringEnterpriseService.health()


@enterprise_admin_bp.route("/metrics", methods=["GET"])
def admin_metrics():
    return MonitoringEnterpriseService.metrics()


@enterprise_admin_bp.route("/tracing", methods=["GET"])
def admin_tracing():
    return MonitoringEnterpriseService.tracing(trace_id=request.args.get("trace_id"))


@enterprise_admin_bp.route("/jobs", methods=["GET"])
def list_jobs():
    return MonitoringEnterpriseService.background_jobs(status=request.args.get("status"))


@enterprise_admin_bp.route("/jobs", methods=["POST"])
def enqueue_job():
    data = request.get_json(silent=True) or {}
    return MonitoringEnterpriseService.enqueue_job(data), 201


@tenants_bp.route("", methods=["GET"])
def list_tenants():
    return TenantEnterpriseService.list_tenants()


@tenants_bp.route("", methods=["POST"])
def create_tenant():
    data = request.get_json(silent=True) or {}
    if not data.get("name"):
        return {"error": "name is required"}, 400
    return TenantEnterpriseService.create(data), 201


@tenants_bp.route("/<tenant_id>", methods=["GET"])
def get_tenant(tenant_id):
    try:
        return TenantEnterpriseService.get(tenant_id)
    except EnterpriseError as exc:
        return _error(exc)


@tenants_bp.route("/<tenant_id>/isolation", methods=["GET"])
def tenant_isolation(tenant_id):
    try:
        return TenantEnterpriseService.isolation(tenant_id)
    except EnterpriseError as exc:
        return _error(exc)


@licenses_bp.route("", methods=["GET"])
def list_licenses():
    return LicenseEnterpriseService.list_licenses(tenant_id=request.args.get("tenant_id"))


@licenses_bp.route("", methods=["POST"])
def create_license():
    data = request.get_json(silent=True) or {}
    return LicenseEnterpriseService.create(data), 201


@licenses_bp.route("/<license_id>", methods=["GET"])
def get_license(license_id):
    try:
        return LicenseEnterpriseService.validate(license_id)
    except EnterpriseError as exc:
        return _error(exc)


@licenses_bp.route("/<license_id>/validate", methods=["POST"])
def validate_license(license_id):
    try:
        return LicenseEnterpriseService.validate(license_id)
    except EnterpriseError as exc:
        return _error(exc)


@enterprise_security_bp.route("/rbac/roles", methods=["GET"])
def rbac_roles():
    return SecurityEnterpriseService.list_rbac_roles(tenant_id=request.args.get("tenant_id"))


@enterprise_security_bp.route("/abac/policies", methods=["GET"])
def abac_policies():
    return SecurityEnterpriseService.list_abac_policies()


@enterprise_security_bp.route("/abac/evaluate", methods=["POST"])
def abac_evaluate():
    data = request.get_json(silent=True) or {}
    return SecurityEnterpriseService.evaluate_abac(data)


@enterprise_security_bp.route("/identity-providers", methods=["GET"])
def identity_providers():
    return SecurityEnterpriseService.list_identity_providers()


@enterprise_security_bp.route("/identity-providers", methods=["POST"])
def create_identity_provider():
    data = request.get_json(silent=True) or {}
    try:
        return SecurityEnterpriseService.create_identity_provider(data), 201
    except EnterpriseError as exc:
        return _error(exc)


@enterprise_security_bp.route("/organizations", methods=["GET"])
def organizations():
    return OrganizationEnterpriseService.list_organizations(tenant_id=request.args.get("tenant_id"))


@enterprise_security_bp.route("/departments", methods=["GET"])
def departments():
    return OrganizationEnterpriseService.list_departments(organization_id=request.args.get("organization_id"))


@enterprise_security_bp.route("/business-units", methods=["GET"])
def business_units():
    return OrganizationEnterpriseService.list_business_units(tenant_id=request.args.get("tenant_id"))


@audit_bp.route("/records", methods=["GET"])
def audit_records():
    return AuditEnterpriseService.list_records(
        tenant_id=request.args.get("tenant_id"),
        limit=int(request.args.get("limit") or 100),
    )


@audit_bp.route("/records", methods=["POST"])
def append_audit_record():
    data = request.get_json(silent=True) or {}
    if not data.get("action"):
        return {"error": "action is required"}, 400
    return AuditEnterpriseService.append_record(
        tenant_id=data.get("tenant_id"),
        actor_email=data.get("actor_email"),
        action=data.get("action"),
        resource_type=data.get("resource_type"),
        resource_id=data.get("resource_id"),
        payload=data.get("payload"),
    ), 201


@audit_bp.route("/access-history", methods=["GET"])
def access_history():
    return AuditEnterpriseService.list_access_history(tenant_id=request.args.get("tenant_id"))


@audit_bp.route("/access-history", methods=["POST"])
def log_access_history():
    data = request.get_json(silent=True) or {}
    return AuditEnterpriseService.log_access(data), 201


@audit_bp.route("/security-events", methods=["GET"])
def security_events():
    return AuditEnterpriseService.list_security_events(tenant_id=request.args.get("tenant_id"))


@audit_bp.route("/security-events", methods=["POST"])
def log_security_event():
    data = request.get_json(silent=True) or {}
    return AuditEnterpriseService.log_security_event(data), 201


@audit_bp.route("/compliance-export", methods=["POST"])
def compliance_export():
    data = request.get_json(silent=True) or {}
    return AuditEnterpriseService.compliance_export(data), 201
