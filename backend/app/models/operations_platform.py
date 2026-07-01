from datetime import datetime
import uuid

from app.extensions.db import db


class ScheduledJob(db.Model):
    __tablename__ = "ops_scheduled_jobs"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    job_code = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(255), nullable=False)
    handler = db.Column(db.String(100), nullable=False)
    cron_expression = db.Column(db.String(100))
    status = db.Column(db.String(50), default="ENABLED")
    timeout_seconds = db.Column(db.Integer, default=300)
    max_retries = db.Column(db.Integer, default=3)
    config_json = db.Column(db.Text, default="{}")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "job_code": self.job_code,
            "name": self.name,
            "handler": self.handler,
            "cron_expression": self.cron_expression,
            "status": self.status,
            "timeout_seconds": self.timeout_seconds,
            "max_retries": self.max_retries,
            "config_json": self.config_json,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class ScheduledJobRun(db.Model):
    __tablename__ = "ops_scheduled_job_runs"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id = db.Column(db.String(36), db.ForeignKey("ops_scheduled_jobs.id"), nullable=False)
    run_code = db.Column(db.String(50), unique=True, nullable=False)
    status = db.Column(db.String(50), default="RUNNING")
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    finished_at = db.Column(db.DateTime)
    duration_ms = db.Column(db.Float, default=0)
    error_message = db.Column(db.Text)
    retry_count = db.Column(db.Integer, default=0)

    def to_dict(self):
        return {
            "id": self.id,
            "job_id": self.job_id,
            "run_code": self.run_code,
            "status": self.status,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "finished_at": self.finished_at.isoformat() if self.finished_at else None,
            "duration_ms": self.duration_ms,
            "error_message": self.error_message,
            "retry_count": self.retry_count,
        }


class ScheduledJobLock(db.Model):
    __tablename__ = "ops_scheduled_job_locks"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id = db.Column(db.String(36), db.ForeignKey("ops_scheduled_jobs.id"), nullable=False, unique=True)
    lock_token = db.Column(db.String(100), nullable=False)
    locked_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime)

    def to_dict(self):
        return {
            "id": self.id,
            "job_id": self.job_id,
            "lock_token": self.lock_token,
            "locked_at": self.locked_at.isoformat() if self.locked_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
        }


class JobExecutionLog(db.Model):
    __tablename__ = "ops_job_execution_logs"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id = db.Column(db.String(36), db.ForeignKey("ops_scheduled_jobs.id"), nullable=False)
    run_id = db.Column(db.String(36), db.ForeignKey("ops_scheduled_job_runs.id"))
    level = db.Column(db.String(20), default="INFO")
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "job_id": self.job_id,
            "run_id": self.run_id,
            "level": self.level,
            "message": self.message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class BackupJob(db.Model):
    __tablename__ = "ops_backup_jobs"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    backup_code = db.Column(db.String(50), unique=True, nullable=False)
    backup_type = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(50), default="COMPLETED")
    manifest_json = db.Column(db.Text, default="{}")
    retention_days = db.Column(db.Integer, default=30)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "backup_code": self.backup_code,
            "backup_type": self.backup_type,
            "status": self.status,
            "manifest_json": self.manifest_json,
            "retention_days": self.retention_days,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class BackupArtifact(db.Model):
    __tablename__ = "ops_backup_artifacts"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    backup_job_id = db.Column(db.String(36), db.ForeignKey("ops_backup_jobs.id"), nullable=False)
    artifact_code = db.Column(db.String(50), unique=True, nullable=False)
    storage_path = db.Column(db.String(500), nullable=False)
    checksum = db.Column(db.String(128), nullable=False)
    size_bytes = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "backup_job_id": self.backup_job_id,
            "artifact_code": self.artifact_code,
            "storage_path": self.storage_path,
            "checksum": self.checksum,
            "size_bytes": self.size_bytes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class RestoreJob(db.Model):
    __tablename__ = "ops_restore_jobs"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    restore_code = db.Column(db.String(50), unique=True, nullable=False)
    backup_job_id = db.Column(db.String(36), db.ForeignKey("ops_backup_jobs.id"), nullable=False)
    mode = db.Column(db.String(50), default="DRY_RUN")
    status = db.Column(db.String(50), default="PENDING")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "restore_code": self.restore_code,
            "backup_job_id": self.backup_job_id,
            "mode": self.mode,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class RestoreValidation(db.Model):
    __tablename__ = "ops_restore_validations"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    restore_job_id = db.Column(db.String(36), db.ForeignKey("ops_restore_jobs.id"), nullable=True)
    validation_code = db.Column(db.String(50), unique=True, nullable=False)
    status = db.Column(db.String(50), default="PASSED")
    detail_json = db.Column(db.Text, default="{}")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "restore_job_id": self.restore_job_id,
            "validation_code": self.validation_code,
            "status": self.status,
            "detail_json": self.detail_json,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class MaintenanceWindow(db.Model):
    __tablename__ = "ops_maintenance_windows"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    window_code = db.Column(db.String(50), unique=True, nullable=False)
    title = db.Column(db.String(255), nullable=False)
    message = db.Column(db.Text)
    status = db.Column(db.String(50), default="SCHEDULED")
    starts_at = db.Column(db.DateTime)
    ends_at = db.Column(db.DateTime)
    active = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "window_code": self.window_code,
            "title": self.title,
            "message": self.message,
            "status": self.status,
            "starts_at": self.starts_at.isoformat() if self.starts_at else None,
            "ends_at": self.ends_at.isoformat() if self.ends_at else None,
            "active": bool(self.active),
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class SecretRotationPlan(db.Model):
    __tablename__ = "ops_secret_rotation_plans"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    secret_name = db.Column(db.String(100), unique=True, nullable=False)
    fingerprint = db.Column(db.String(128), nullable=False)
    rotation_interval_days = db.Column(db.Integer, default=90)
    last_rotated_at = db.Column(db.DateTime)
    expires_at = db.Column(db.DateTime)
    status = db.Column(db.String(50), default="ACTIVE")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "secret_name": self.secret_name,
            "fingerprint": self.fingerprint,
            "rotation_interval_days": self.rotation_interval_days,
            "last_rotated_at": self.last_rotated_at.isoformat() if self.last_rotated_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class SecretRotationEvent(db.Model):
    __tablename__ = "ops_secret_rotation_events"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    plan_id = db.Column(db.String(36), db.ForeignKey("ops_secret_rotation_plans.id"), nullable=False)
    event_code = db.Column(db.String(50), unique=True, nullable=False)
    action = db.Column(db.String(50), nullable=False)
    fingerprint = db.Column(db.String(128), nullable=False)
    detail_json = db.Column(db.Text, default="{}")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "plan_id": self.plan_id,
            "event_code": self.event_code,
            "action": self.action,
            "fingerprint": self.fingerprint,
            "detail_json": self.detail_json,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class DeploymentRecord(db.Model):
    __tablename__ = "ops_deployment_records"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    deployment_code = db.Column(db.String(50), unique=True, nullable=False)
    version = db.Column(db.String(50), nullable=False)
    build_sha = db.Column(db.String(100))
    build_time = db.Column(db.DateTime)
    environment = db.Column(db.String(50), default="production")
    status = db.Column(db.String(50), default="SUCCESS")
    readiness_score = db.Column(db.Float, default=100.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "deployment_code": self.deployment_code,
            "version": self.version,
            "build_sha": self.build_sha,
            "build_time": self.build_time.isoformat() if self.build_time else None,
            "environment": self.environment,
            "status": self.status,
            "readiness_score": self.readiness_score,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class DeploymentCheck(db.Model):
    __tablename__ = "ops_deployment_checks"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    deployment_id = db.Column(db.String(36), db.ForeignKey("ops_deployment_records.id"), nullable=False)
    check_code = db.Column(db.String(50), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(50), default="PASSED")
    detail_json = db.Column(db.Text, default="{}")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "deployment_id": self.deployment_id,
            "check_code": self.check_code,
            "name": self.name,
            "status": self.status,
            "detail_json": self.detail_json,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class DeploymentRollbackPlan(db.Model):
    __tablename__ = "ops_deployment_rollback_plans"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    deployment_id = db.Column(db.String(36), db.ForeignKey("ops_deployment_records.id"), nullable=False)
    plan_code = db.Column(db.String(50), unique=True, nullable=False)
    target_version = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(50), default="READY")
    detail_json = db.Column(db.Text, default="{}")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "deployment_id": self.deployment_id,
            "plan_code": self.plan_code,
            "target_version": self.target_version,
            "status": self.status,
            "detail_json": self.detail_json,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
