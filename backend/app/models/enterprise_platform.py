from datetime import datetime
import hashlib
import uuid

from app.extensions.db import db


class EnterpriseTenant(db.Model):
    __tablename__ = "enterprise_tenants"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_code = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(50), default="ACTIVE")
    isolation_mode = db.Column(db.String(50), default="STRICT")
    schema_name = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "tenant_code": self.tenant_code,
            "name": self.name,
            "status": self.status,
            "isolation_mode": self.isolation_mode,
            "schema_name": self.schema_name,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class EnterpriseOrganization(db.Model):
    __tablename__ = "enterprise_organizations"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = db.Column(db.String(36), db.ForeignKey("enterprise_tenants.id"))
    org_code = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(255), nullable=False)
    parent_org_id = db.Column(db.String(36))
    level = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "tenant_id": self.tenant_id,
            "org_code": self.org_code,
            "name": self.name,
            "parent_org_id": self.parent_org_id,
            "level": self.level,
            "is_active": bool(self.is_active),
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class EnterpriseDepartment(db.Model):
    __tablename__ = "enterprise_departments"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = db.Column(db.String(36), db.ForeignKey("enterprise_organizations.id"))
    dept_code = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(255), nullable=False)
    parent_dept_id = db.Column(db.String(36))
    level = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "organization_id": self.organization_id,
            "dept_code": self.dept_code,
            "name": self.name,
            "parent_dept_id": self.parent_dept_id,
            "level": self.level,
            "is_active": bool(self.is_active),
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class EnterpriseBusinessUnit(db.Model):
    __tablename__ = "enterprise_business_units"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = db.Column(db.String(36), db.ForeignKey("enterprise_tenants.id"))
    unit_code = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(255), nullable=False)
    organization_id = db.Column(db.String(36))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "tenant_id": self.tenant_id,
            "unit_code": self.unit_code,
            "name": self.name,
            "organization_id": self.organization_id,
            "is_active": bool(self.is_active),
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class EnterpriseRole(db.Model):
    __tablename__ = "enterprise_roles"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = db.Column(db.String(36))
    role_code = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(255), nullable=False)
    permissions_json = db.Column(db.Text, default="[]")
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "tenant_id": self.tenant_id,
            "role_code": self.role_code,
            "name": self.name,
            "permissions_json": self.permissions_json,
            "is_active": bool(self.is_active),
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class EnterpriseAbacPolicy(db.Model):
    __tablename__ = "enterprise_abac_policies"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    policy_code = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(255), nullable=False)
    resource = db.Column(db.String(100))
    action = db.Column(db.String(100))
    condition_json = db.Column(db.Text, default="{}")
    effect = db.Column(db.String(20), default="ALLOW")
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "policy_code": self.policy_code,
            "name": self.name,
            "resource": self.resource,
            "action": self.action,
            "condition_json": self.condition_json,
            "effect": self.effect,
            "is_active": bool(self.is_active),
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class EnterpriseIdentityProvider(db.Model):
    __tablename__ = "enterprise_identity_providers"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    provider_code = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(255), nullable=False)
    provider_type = db.Column(db.String(20), nullable=False)
    issuer_url = db.Column(db.String(500))
    client_id = db.Column(db.String(255))
    metadata_json = db.Column(db.Text, default="{}")
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "provider_code": self.provider_code,
            "name": self.name,
            "provider_type": self.provider_type,
            "issuer_url": self.issuer_url,
            "client_id": self.client_id,
            "metadata_json": self.metadata_json,
            "is_active": bool(self.is_active),
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class EnterpriseLicense(db.Model):
    __tablename__ = "enterprise_licenses"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    license_key = db.Column(db.String(100), unique=True, nullable=False)
    tenant_id = db.Column(db.String(36))
    plan_code = db.Column(db.String(50), nullable=False)
    seat_limit = db.Column(db.Integer, default=100)
    feature_flags_json = db.Column(db.Text, default="[]")
    status = db.Column(db.String(50), default="ACTIVE")
    expires_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "license_key": self.license_key,
            "tenant_id": self.tenant_id,
            "plan_code": self.plan_code,
            "seat_limit": self.seat_limit,
            "feature_flags_json": self.feature_flags_json,
            "status": self.status,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class EnterpriseFeatureFlag(db.Model):
    __tablename__ = "enterprise_feature_flags"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    flag_code = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(255), nullable=False)
    enabled = db.Column(db.Boolean, default=False)
    tenant_id = db.Column(db.String(36))
    rollout_percent = db.Column(db.Integer, default=100)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "flag_code": self.flag_code,
            "name": self.name,
            "enabled": bool(self.enabled),
            "tenant_id": self.tenant_id,
            "rollout_percent": self.rollout_percent,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class EnterpriseSystemSetting(db.Model):
    __tablename__ = "enterprise_system_settings"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    setting_key = db.Column(db.String(100), unique=True, nullable=False)
    setting_value = db.Column(db.Text)
    category = db.Column(db.String(50), default="GENERAL")
    is_secret = db.Column(db.Boolean, default=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "setting_key": self.setting_key,
            "setting_value": "***" if self.is_secret else self.setting_value,
            "category": self.category,
            "is_secret": bool(self.is_secret),
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class EnterpriseAuditRecord(db.Model):
    __tablename__ = "enterprise_audit_records"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    record_hash = db.Column(db.String(64), unique=True, nullable=False)
    tenant_id = db.Column(db.String(36))
    actor_email = db.Column(db.String(255))
    action = db.Column(db.String(100), nullable=False)
    resource_type = db.Column(db.String(100))
    resource_id = db.Column(db.String(36))
    payload_json = db.Column(db.Text, default="{}")
    previous_hash = db.Column(db.String(64))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "record_hash": self.record_hash,
            "tenant_id": self.tenant_id,
            "actor_email": self.actor_email,
            "action": self.action,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "payload_json": self.payload_json,
            "previous_hash": self.previous_hash,
            "immutable": True,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class EnterpriseAccessHistory(db.Model):
    __tablename__ = "enterprise_access_history"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = db.Column(db.String(36))
    user_email = db.Column(db.String(255))
    resource = db.Column(db.String(255))
    action = db.Column(db.String(100))
    ip_address = db.Column(db.String(100))
    success = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "tenant_id": self.tenant_id,
            "user_email": self.user_email,
            "resource": self.resource,
            "action": self.action,
            "ip_address": self.ip_address,
            "success": bool(self.success),
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class EnterpriseSecurityEvent(db.Model):
    __tablename__ = "enterprise_security_events"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    event_code = db.Column(db.String(50), unique=True, nullable=False)
    tenant_id = db.Column(db.String(36))
    event_type = db.Column(db.String(50), nullable=False)
    severity = db.Column(db.String(20), default="INFO")
    message = db.Column(db.Text)
    metadata_json = db.Column(db.Text, default="{}")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "event_code": self.event_code,
            "tenant_id": self.tenant_id,
            "event_type": self.event_type,
            "severity": self.severity,
            "message": self.message,
            "metadata_json": self.metadata_json,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class EnterpriseComplianceExport(db.Model):
    __tablename__ = "enterprise_compliance_exports"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    export_code = db.Column(db.String(50), unique=True, nullable=False)
    tenant_id = db.Column(db.String(36))
    export_type = db.Column(db.String(50), default="AUDIT")
    status = db.Column(db.String(50), default="COMPLETED")
    record_count = db.Column(db.Integer, default=0)
    file_path = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "export_code": self.export_code,
            "tenant_id": self.tenant_id,
            "export_type": self.export_type,
            "status": self.status,
            "record_count": self.record_count,
            "file_path": self.file_path,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class EnterpriseUsageMetric(db.Model):
    __tablename__ = "enterprise_usage_metrics"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = db.Column(db.String(36))
    metric_code = db.Column(db.String(50), nullable=False)
    metric_value = db.Column(db.Float, default=0)
    period = db.Column(db.String(20), default="DAILY")
    recorded_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "tenant_id": self.tenant_id,
            "metric_code": self.metric_code,
            "metric_value": self.metric_value,
            "period": self.period,
            "recorded_at": self.recorded_at.isoformat() if self.recorded_at else None,
        }


class EnterpriseBackgroundJob(db.Model):
    __tablename__ = "enterprise_background_jobs"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    job_code = db.Column(db.String(50), unique=True, nullable=False)
    job_type = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(50), default="PENDING")
    trace_id = db.Column(db.String(36))
    payload_json = db.Column(db.Text, default="{}")
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "job_code": self.job_code,
            "job_type": self.job_type,
            "status": self.status,
            "trace_id": self.trace_id,
            "payload_json": self.payload_json,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


def compute_audit_hash(payload, previous_hash=None):
    raw = f"{previous_hash or ''}|{payload}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()
