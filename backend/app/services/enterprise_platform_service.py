import json
import uuid
from datetime import datetime, timedelta

from app.core.statuses import (
    ENTERPRISE_HEALTH_OK,
    ENTERPRISE_IDENTITY_OAUTH2,
    ENTERPRISE_IDENTITY_OIDC,
    ENTERPRISE_IDENTITY_SAML,
    ENTERPRISE_JOB_COMPLETED,
    ENTERPRISE_JOB_PENDING,
    ENTERPRISE_JOB_RUNNING,
    ENTERPRISE_LICENSE_ACTIVE,
    ENTERPRISE_TENANT_ACTIVE,
)
from app.extensions.db import db
from app.models.enterprise_platform import (
    EnterpriseAbacPolicy,
    EnterpriseAccessHistory,
    EnterpriseAuditRecord,
    EnterpriseBackgroundJob,
    EnterpriseBusinessUnit,
    EnterpriseComplianceExport,
    EnterpriseDepartment,
    EnterpriseFeatureFlag,
    EnterpriseIdentityProvider,
    EnterpriseLicense,
    EnterpriseOrganization,
    EnterpriseRole,
    EnterpriseSecurityEvent,
    EnterpriseSystemSetting,
    EnterpriseTenant,
    EnterpriseUsageMetric,
    compute_audit_hash,
)


class EnterpriseError(Exception):

    def __init__(self, message, status_code=400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class EnterprisePlatformService:

    @staticmethod
    def ensure_defaults():
        if EnterpriseTenant.query.first():
            return {"seeded": False}

        tenant = EnterpriseTenant(
            tenant_code="TEN-DXCON",
            name="DxCon Enterprise",
            status=ENTERPRISE_TENANT_ACTIVE,
            isolation_mode="STRICT",
            schema_name="tenant_dxcon",
        )
        db.session.add(tenant)
        db.session.flush()

        root_org = EnterpriseOrganization(
            tenant_id=tenant.id,
            org_code="ORG-ROOT",
            name="DxCon Group",
            level=0,
        )
        db.session.add(root_org)
        db.session.flush()

        child_org = EnterpriseOrganization(
            tenant_id=tenant.id,
            org_code="ORG-LAB",
            name="Laboratory Division",
            parent_org_id=root_org.id,
            level=1,
        )
        db.session.add(child_org)
        db.session.flush()

        root_dept = EnterpriseDepartment(
            organization_id=root_org.id,
            dept_code="DEPT-ADMIN",
            name="Administration",
            level=0,
        )
        db.session.add(root_dept)
        db.session.flush()

        db.session.add(
            EnterpriseDepartment(
                organization_id=root_org.id,
                dept_code="DEPT-LIS",
                name="Laboratory Information Systems",
                parent_dept_id=root_dept.id,
                level=1,
            )
        )

        db.session.add(
            EnterpriseBusinessUnit(
                tenant_id=tenant.id,
                unit_code="BU-DIAGNOSTICS",
                name="Diagnostics",
                organization_id=child_org.id,
            )
        )

        db.session.add(
            EnterpriseRole(
                tenant_id=tenant.id,
                role_code="ROLE-ADMIN",
                name="Enterprise Admin",
                permissions_json=json.dumps(["admin:*", "tenant:manage", "audit:read"]),
            )
        )
        db.session.add(
            EnterpriseRole(
                tenant_id=tenant.id,
                role_code="ROLE-ANALYST",
                name="Lab Analyst",
                permissions_json=json.dumps(["lab:read", "results:write"]),
            )
        )

        db.session.add(
            EnterpriseAbacPolicy(
                policy_code="ABAC-LAB-READ",
                name="Lab read by department",
                resource="lab_result",
                action="read",
                condition_json=json.dumps({"department": "DEPT-LIS", "tenant_match": True}),
                effect="ALLOW",
            )
        )

        for provider_type, code, name in (
            (ENTERPRISE_IDENTITY_OIDC, "IDP-OIDC", "OpenID Connect"),
            (ENTERPRISE_IDENTITY_OAUTH2, "IDP-OAUTH2", "OAuth2 Provider"),
            (ENTERPRISE_IDENTITY_SAML, "IDP-SAML", "SAML SSO"),
        ):
            db.session.add(
                EnterpriseIdentityProvider(
                    provider_code=code,
                    name=name,
                    provider_type=provider_type,
                    issuer_url=f"https://idp.example.com/{provider_type.lower()}",
                    client_id=f"dxcon-{provider_type.lower()}",
                    metadata_json=json.dumps({"protocol": provider_type}),
                )
            )

        db.session.add(
            EnterpriseLicense(
                license_key=f"LIC-{uuid.uuid4().hex[:12].upper()}",
                tenant_id=tenant.id,
                plan_code="ENTERPRISE",
                seat_limit=500,
                feature_flags_json=json.dumps(["AI_CDS", "FEDERATION", "KNOWLEDGE_ENGINE"]),
                status=ENTERPRISE_LICENSE_ACTIVE,
                expires_at=datetime.utcnow() + timedelta(days=365),
            )
        )

        for flag_code, name, enabled in (
            ("FF-AI-CDS", "AI Clinical Decision Support", True),
            ("FF-FEDERATION", "Multi-Lab Federation", True),
            ("FF-KNOWLEDGE", "Knowledge Engine", True),
            ("FF-BETA-PORTAL", "Beta Portal", False),
        ):
            db.session.add(
                EnterpriseFeatureFlag(
                    flag_code=flag_code,
                    name=name,
                    enabled=enabled,
                    tenant_id=tenant.id,
                )
            )

        settings = [
            ("system.timezone", "Asia/Ho_Chi_Minh", "GENERAL"),
            ("security.session_timeout_minutes", "30", "SECURITY"),
            ("audit.retention_days", "2555", "COMPLIANCE"),
        ]
        for key, value, category in settings:
            db.session.add(
                EnterpriseSystemSetting(setting_key=key, setting_value=value, category=category)
            )

        for metric_code, value in (("API_REQUESTS", 12500), ("ACTIVE_USERS", 240), ("STORAGE_GB", 85.5)):
            db.session.add(
                EnterpriseUsageMetric(tenant_id=tenant.id, metric_code=metric_code, metric_value=value)
            )

        db.session.add(
            EnterpriseBackgroundJob(
                job_code=f"JOB-{uuid.uuid4().hex[:8].upper()}",
                job_type="AUDIT_EXPORT",
                status=ENTERPRISE_JOB_COMPLETED,
                trace_id=str(uuid.uuid4()),
                started_at=datetime.utcnow() - timedelta(minutes=5),
                completed_at=datetime.utcnow(),
            )
        )

        db.session.commit()
        AuditEnterpriseService.append_record(
            tenant_id=tenant.id,
            actor_email="system@dxcon.local",
            action="ENTERPRISE_SEED",
            resource_type="Tenant",
            resource_id=tenant.id,
            payload={"message": "Enterprise platform initialized"},
        )
        return {"seeded": True, "tenant_id": tenant.id}


class TenantEnterpriseService:

    @staticmethod
    def list_tenants():
        EnterprisePlatformService.ensure_defaults()
        rows = EnterpriseTenant.query.order_by(EnterpriseTenant.created_at.desc()).all()
        return {"count": len(rows), "tenants": [row.to_dict() for row in rows]}

    @staticmethod
    def create(data):
        code = data.get("tenant_code") or f"TEN-{uuid.uuid4().hex[:8].upper()}"
        row = EnterpriseTenant(
            tenant_code=code,
            name=data.get("name") or code,
            status=data.get("status") or ENTERPRISE_TENANT_ACTIVE,
            isolation_mode=data.get("isolation_mode") or "STRICT",
            schema_name=data.get("schema_name") or f"tenant_{code.lower()}",
        )
        db.session.add(row)
        db.session.commit()
        return row.to_dict()

    @staticmethod
    def get(tenant_id):
        row = EnterpriseTenant.query.get(tenant_id)
        if not row:
            raise EnterpriseError("Tenant not found", 404)
        return row.to_dict()

    @staticmethod
    def isolation(tenant_id):
        tenant = TenantEnterpriseService.get(tenant_id)
        orgs = EnterpriseOrganization.query.filter_by(tenant_id=tenant_id).count()
        units = EnterpriseBusinessUnit.query.filter_by(tenant_id=tenant_id).count()
        return {
            "tenant": tenant,
            "isolation_mode": tenant["isolation_mode"],
            "schema_name": tenant["schema_name"],
            "organization_count": orgs,
            "business_unit_count": units,
            "isolated": tenant["isolation_mode"] == "STRICT",
        }


class OrganizationEnterpriseService:

    @staticmethod
    def list_organizations(tenant_id=None):
        EnterprisePlatformService.ensure_defaults()
        q = EnterpriseOrganization.query
        if tenant_id:
            q = q.filter_by(tenant_id=tenant_id)
        rows = q.order_by(EnterpriseOrganization.level.asc()).all()
        return {"count": len(rows), "organizations": [row.to_dict() for row in rows]}

    @staticmethod
    def list_departments(organization_id=None):
        EnterprisePlatformService.ensure_defaults()
        q = EnterpriseDepartment.query
        if organization_id:
            q = q.filter_by(organization_id=organization_id)
        rows = q.order_by(EnterpriseDepartment.level.asc()).all()
        return {"count": len(rows), "departments": [row.to_dict() for row in rows]}

    @staticmethod
    def list_business_units(tenant_id=None):
        EnterprisePlatformService.ensure_defaults()
        q = EnterpriseBusinessUnit.query
        if tenant_id:
            q = q.filter_by(tenant_id=tenant_id)
        rows = q.all()
        return {"count": len(rows), "business_units": [row.to_dict() for row in rows]}


class SecurityEnterpriseService:

    @staticmethod
    def list_rbac_roles(tenant_id=None):
        EnterprisePlatformService.ensure_defaults()
        q = EnterpriseRole.query.filter_by(is_active=True)
        if tenant_id:
            q = q.filter_by(tenant_id=tenant_id)
        rows = q.all()
        return {
            "count": len(rows),
            "roles": [
                {**row.to_dict(), "permissions": json.loads(row.permissions_json or "[]")}
                for row in rows
            ],
        }

    @staticmethod
    def list_abac_policies():
        EnterprisePlatformService.ensure_defaults()
        rows = EnterpriseAbacPolicy.query.filter_by(is_active=True).all()
        return {
            "count": len(rows),
            "policies": [
                {**row.to_dict(), "conditions": json.loads(row.condition_json or "{}")}
                for row in rows
            ],
        }

    @staticmethod
    def evaluate_abac(data):
        policies = SecurityEnterpriseService.list_abac_policies()["policies"]
        resource = data.get("resource")
        action = data.get("action")
        context = data.get("context") or {}
        for policy in policies:
            if policy["resource"] == resource and policy["action"] == action:
                conditions = policy.get("conditions") or {}
                if conditions.get("tenant_match") and not context.get("tenant_id"):
                    continue
                if conditions.get("department") and context.get("department") != conditions["department"]:
                    continue
                return {"effect": policy["effect"], "policy_code": policy["policy_code"]}
        return {"effect": "DENY", "policy_code": None}

    @staticmethod
    def list_identity_providers():
        EnterprisePlatformService.ensure_defaults()
        rows = EnterpriseIdentityProvider.query.filter_by(is_active=True).all()
        return {"count": len(rows), "providers": [row.to_dict() for row in rows]}

    @staticmethod
    def create_identity_provider(data):
        provider_type = (data.get("provider_type") or "").upper()
        if provider_type not in (ENTERPRISE_IDENTITY_OIDC, ENTERPRISE_IDENTITY_OAUTH2, ENTERPRISE_IDENTITY_SAML):
            raise EnterpriseError("provider_type must be OIDC, OAUTH2, or SAML")
        code = data.get("provider_code") or f"IDP-{uuid.uuid4().hex[:8].upper()}"
        row = EnterpriseIdentityProvider(
            provider_code=code,
            name=data.get("name") or code,
            provider_type=provider_type,
            issuer_url=data.get("issuer_url"),
            client_id=data.get("client_id"),
            metadata_json=json.dumps(data.get("metadata") or {}),
        )
        db.session.add(row)
        db.session.commit()
        return row.to_dict()


class LicenseEnterpriseService:

    @staticmethod
    def list_licenses(tenant_id=None):
        EnterprisePlatformService.ensure_defaults()
        q = EnterpriseLicense.query
        if tenant_id:
            q = q.filter_by(tenant_id=tenant_id)
        rows = q.order_by(EnterpriseLicense.created_at.desc()).all()
        return {"count": len(rows), "licenses": [row.to_dict() for row in rows]}

    @staticmethod
    def create(data):
        row = EnterpriseLicense(
            license_key=data.get("license_key") or f"LIC-{uuid.uuid4().hex[:12].upper()}",
            tenant_id=data.get("tenant_id"),
            plan_code=data.get("plan_code") or "ENTERPRISE",
            seat_limit=int(data.get("seat_limit") or 100),
            feature_flags_json=json.dumps(data.get("features") or []),
            status=data.get("status") or ENTERPRISE_LICENSE_ACTIVE,
            expires_at=datetime.utcnow() + timedelta(days=int(data.get("valid_days") or 365)),
        )
        db.session.add(row)
        db.session.commit()
        return row.to_dict()

    @staticmethod
    def validate(license_id):
        row = EnterpriseLicense.query.get(license_id)
        if not row:
            raise EnterpriseError("License not found", 404)
        valid = row.status == ENTERPRISE_LICENSE_ACTIVE and (
            not row.expires_at or row.expires_at > datetime.utcnow()
        )
        return {
            "license": row.to_dict(),
            "valid": valid,
            "features": json.loads(row.feature_flags_json or "[]"),
        }


class AdminEnterpriseService:

    @staticmethod
    def overview():
        EnterprisePlatformService.ensure_defaults()
        tenant = EnterpriseTenant.query.first()
        return {
            "tenants": EnterpriseTenant.query.count(),
            "organizations": EnterpriseOrganization.query.count(),
            "licenses": EnterpriseLicense.query.filter_by(status=ENTERPRISE_LICENSE_ACTIVE).count(),
            "feature_flags": EnterpriseFeatureFlag.query.count(),
            "audit_records": EnterpriseAuditRecord.query.count(),
            "background_jobs": EnterpriseBackgroundJob.query.count(),
            "primary_tenant": tenant.to_dict() if tenant else None,
        }

    @staticmethod
    def list_settings():
        EnterprisePlatformService.ensure_defaults()
        rows = EnterpriseSystemSetting.query.order_by(EnterpriseSystemSetting.category.asc()).all()
        return {"count": len(rows), "settings": [row.to_dict() for row in rows]}

    @staticmethod
    def upsert_setting(data):
        key = data.get("setting_key")
        if not key:
            raise EnterpriseError("setting_key is required")
        row = EnterpriseSystemSetting.query.filter_by(setting_key=key).first()
        if not row:
            row = EnterpriseSystemSetting(setting_key=key)
            db.session.add(row)
        row.setting_value = data.get("setting_value")
        row.category = data.get("category") or row.category or "GENERAL"
        row.is_secret = bool(data.get("is_secret"))
        row.updated_at = datetime.utcnow()
        db.session.commit()
        return row.to_dict()

    @staticmethod
    def list_feature_flags(tenant_id=None):
        EnterprisePlatformService.ensure_defaults()
        q = EnterpriseFeatureFlag.query
        if tenant_id:
            q = q.filter_by(tenant_id=tenant_id)
        rows = q.all()
        return {"count": len(rows), "feature_flags": [row.to_dict() for row in rows]}

    @staticmethod
    def upsert_feature_flag(data):
        code = data.get("flag_code") or f"FF-{uuid.uuid4().hex[:8].upper()}"
        row = EnterpriseFeatureFlag.query.filter_by(flag_code=code).first()
        if not row:
            row = EnterpriseFeatureFlag(flag_code=code, name=data.get("name") or code)
            db.session.add(row)
        row.enabled = bool(data.get("enabled", row.enabled))
        row.tenant_id = data.get("tenant_id") or row.tenant_id
        row.rollout_percent = int(data.get("rollout_percent") or row.rollout_percent or 100)
        db.session.commit()
        return row.to_dict()

    @staticmethod
    def usage_statistics(tenant_id=None):
        EnterprisePlatformService.ensure_defaults()
        q = EnterpriseUsageMetric.query
        if tenant_id:
            q = q.filter_by(tenant_id=tenant_id)
        rows = q.order_by(EnterpriseUsageMetric.recorded_at.desc()).all()
        return {"count": len(rows), "metrics": [row.to_dict() for row in rows]}


class AuditEnterpriseService:

    @staticmethod
    def append_record(tenant_id=None, actor_email=None, action=None, resource_type=None, resource_id=None, payload=None):
        last = EnterpriseAuditRecord.query.order_by(EnterpriseAuditRecord.created_at.desc()).first()
        previous_hash = last.record_hash if last else None
        payload_json = json.dumps(payload or {}, sort_keys=True)
        record_hash = compute_audit_hash(payload_json, previous_hash)
        row = EnterpriseAuditRecord(
            record_hash=record_hash,
            tenant_id=tenant_id,
            actor_email=actor_email,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            payload_json=payload_json,
            previous_hash=previous_hash,
        )
        db.session.add(row)
        db.session.commit()
        return row.to_dict()

    @staticmethod
    def list_records(tenant_id=None, limit=100):
        EnterprisePlatformService.ensure_defaults()
        q = EnterpriseAuditRecord.query
        if tenant_id:
            q = q.filter_by(tenant_id=tenant_id)
        rows = q.order_by(EnterpriseAuditRecord.created_at.desc()).limit(limit).all()
        return {"count": len(rows), "records": [row.to_dict() for row in rows]}

    @staticmethod
    def log_access(data):
        row = EnterpriseAccessHistory(
            tenant_id=data.get("tenant_id"),
            user_email=data.get("user_email"),
            resource=data.get("resource"),
            action=data.get("action"),
            ip_address=data.get("ip_address"),
            success=bool(data.get("success", True)),
        )
        db.session.add(row)
        db.session.commit()
        return row.to_dict()

    @staticmethod
    def list_access_history(tenant_id=None):
        EnterprisePlatformService.ensure_defaults()
        q = EnterpriseAccessHistory.query
        if tenant_id:
            q = q.filter_by(tenant_id=tenant_id)
        rows = q.order_by(EnterpriseAccessHistory.created_at.desc()).limit(100).all()
        return {"count": len(rows), "access_history": [row.to_dict() for row in rows]}

    @staticmethod
    def log_security_event(data):
        row = EnterpriseSecurityEvent(
            event_code=f"SEC-{uuid.uuid4().hex[:10].upper()}",
            tenant_id=data.get("tenant_id"),
            event_type=data.get("event_type") or "ACCESS",
            severity=data.get("severity") or "INFO",
            message=data.get("message"),
            metadata_json=json.dumps(data.get("metadata") or {}),
        )
        db.session.add(row)
        db.session.commit()
        return row.to_dict()

    @staticmethod
    def list_security_events(tenant_id=None):
        EnterprisePlatformService.ensure_defaults()
        q = EnterpriseSecurityEvent.query
        if tenant_id:
            q = q.filter_by(tenant_id=tenant_id)
        rows = q.order_by(EnterpriseSecurityEvent.created_at.desc()).limit(100).all()
        return {"count": len(rows), "security_events": [row.to_dict() for row in rows]}

    @staticmethod
    def compliance_export(data):
        tenant_id = data.get("tenant_id")
        records = AuditEnterpriseService.list_records(tenant_id=tenant_id)["records"]
        export = EnterpriseComplianceExport(
            export_code=f"EXP-{uuid.uuid4().hex[:10].upper()}",
            tenant_id=tenant_id,
            export_type=data.get("export_type") or "AUDIT",
            status="COMPLETED",
            record_count=len(records),
            file_path=f"/exports/compliance/{uuid.uuid4().hex}.json",
        )
        db.session.add(export)
        db.session.commit()
        return export.to_dict()


class MonitoringEnterpriseService:

    @staticmethod
    def health():
        EnterprisePlatformService.ensure_defaults()
        db_ok = db.session.execute(db.text("SELECT 1")).scalar() == 1
        return {
            "status": ENTERPRISE_HEALTH_OK if db_ok else "DEGRADED",
            "database": "ok" if db_ok else "error",
            "timestamp": datetime.utcnow().isoformat(),
        }

    @staticmethod
    def metrics():
        EnterprisePlatformService.ensure_defaults()
        return {
            "tenants": EnterpriseTenant.query.count(),
            "audit_records": EnterpriseAuditRecord.query.count(),
            "security_events": EnterpriseSecurityEvent.query.count(),
            "pending_jobs": EnterpriseBackgroundJob.query.filter_by(status=ENTERPRISE_JOB_PENDING).count(),
            "running_jobs": EnterpriseBackgroundJob.query.filter_by(status=ENTERPRISE_JOB_RUNNING).count(),
        }

    @staticmethod
    def tracing(trace_id=None):
        q = EnterpriseBackgroundJob.query
        if trace_id:
            q = q.filter_by(trace_id=trace_id)
        rows = q.order_by(EnterpriseBackgroundJob.created_at.desc()).limit(20).all()
        return {"count": len(rows), "traces": [row.to_dict() for row in rows]}

    @staticmethod
    def background_jobs(status=None):
        EnterprisePlatformService.ensure_defaults()
        q = EnterpriseBackgroundJob.query
        if status:
            q = q.filter_by(status=status.upper())
        rows = q.order_by(EnterpriseBackgroundJob.created_at.desc()).limit(100).all()
        return {"count": len(rows), "jobs": [row.to_dict() for row in rows]}

    @staticmethod
    def enqueue_job(data):
        row = EnterpriseBackgroundJob(
            job_code=data.get("job_code") or f"JOB-{uuid.uuid4().hex[:8].upper()}",
            job_type=data.get("job_type") or "GENERIC",
            status=ENTERPRISE_JOB_PENDING,
            trace_id=data.get("trace_id") or str(uuid.uuid4()),
            payload_json=json.dumps(data.get("payload") or {}),
        )
        db.session.add(row)
        db.session.commit()
        row.status = ENTERPRISE_JOB_RUNNING
        row.started_at = datetime.utcnow()
        row.status = ENTERPRISE_JOB_COMPLETED
        row.completed_at = datetime.utcnow()
        db.session.commit()
        return row.to_dict()
