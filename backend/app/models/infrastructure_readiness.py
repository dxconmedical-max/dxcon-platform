from datetime import datetime
import uuid

from app.extensions.db import db


class RecoveryPlan(db.Model):
    __tablename__ = "infra_recovery_plans"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    plan_code = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(255), nullable=False)
    rto_minutes = db.Column(db.Integer, default=60)
    rpo_minutes = db.Column(db.Integer, default=15)
    status = db.Column(db.String(50), default="ACTIVE")
    detail_json = db.Column(db.Text, default="{}")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "plan_code": self.plan_code,
            "name": self.name,
            "rto_minutes": self.rto_minutes,
            "rpo_minutes": self.rpo_minutes,
            "status": self.status,
            "detail_json": self.detail_json,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class RecoveryTest(db.Model):
    __tablename__ = "infra_recovery_tests"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    plan_id = db.Column(db.String(36), db.ForeignKey("infra_recovery_plans.id"), nullable=False)
    test_code = db.Column(db.String(50), unique=True, nullable=False)
    status = db.Column(db.String(50), default="PASSED")
    mode = db.Column(db.String(50), default="DRY_RUN")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "plan_id": self.plan_id,
            "test_code": self.test_code,
            "status": self.status,
            "mode": self.mode,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class RecoveryArtifact(db.Model):
    __tablename__ = "infra_recovery_artifacts"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    plan_id = db.Column(db.String(36), db.ForeignKey("infra_recovery_plans.id"), nullable=False)
    artifact_code = db.Column(db.String(50), unique=True, nullable=False)
    artifact_type = db.Column(db.String(50), nullable=False)
    checksum = db.Column(db.String(128), nullable=False)
    storage_path = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "plan_id": self.plan_id,
            "artifact_code": self.artifact_code,
            "artifact_type": self.artifact_type,
            "checksum": self.checksum,
            "storage_path": self.storage_path,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class RecoveryReport(db.Model):
    __tablename__ = "infra_recovery_reports"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    plan_id = db.Column(db.String(36), db.ForeignKey("infra_recovery_plans.id"), nullable=False)
    report_code = db.Column(db.String(50), unique=True, nullable=False)
    status = db.Column(db.String(50), default="COMPLETED")
    summary_json = db.Column(db.Text, default="{}")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "plan_id": self.plan_id,
            "report_code": self.report_code,
            "status": self.status,
            "summary_json": self.summary_json,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
