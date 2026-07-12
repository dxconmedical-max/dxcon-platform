"""Clinical governance models — Release 8.0 Sprint 6."""

from __future__ import annotations

import uuid
from datetime import datetime

from app.extensions.db import db


class ClinicalWorkflowTransition(db.Model):
    __tablename__ = "clinical_workflow_transitions"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = db.Column(db.String(36), nullable=False, index=True)
    aggregate_type = db.Column(db.String(50), nullable=False)
    aggregate_id = db.Column(db.String(36), nullable=False, index=True)
    from_status = db.Column(db.String(50))
    to_status = db.Column(db.String(50), nullable=False)
    actor = db.Column(db.String(255), nullable=False)
    reason = db.Column(db.Text)
    correlation_id = db.Column(db.String(64))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "aggregate_type": self.aggregate_type,
            "aggregate_id": self.aggregate_id,
            "from_status": self.from_status,
            "to_status": self.to_status,
            "actor": self.actor,
            "reason": self.reason,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class CriticalValuePolicy(db.Model):
    __tablename__ = "critical_value_policies"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = db.Column(db.String(36), nullable=False, index=True)
    policy_code = db.Column(db.String(50), unique=True, nullable=False)
    test_code = db.Column(db.String(50))
    analyte = db.Column(db.String(100))
    lower_threshold = db.Column(db.Float)
    upper_threshold = db.Column(db.Float)
    sex = db.Column(db.String(10))
    age_min = db.Column(db.Integer)
    age_max = db.Column(db.Integer)
    notification_recipients_json = db.Column(db.Text)
    acknowledgement_sla_minutes = db.Column(db.Integer, default=60)
    escalation_schedule_json = db.Column(db.Text)
    version = db.Column(db.Integer, default=1)
    approved_by = db.Column(db.String(255))
    effective_at = db.Column(db.DateTime)
    status = db.Column(db.String(30), default="ACTIVE")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "policy_code": self.policy_code,
            "test_code": self.test_code,
            "analyte": self.analyte,
            "lower_threshold": self.lower_threshold,
            "upper_threshold": self.upper_threshold,
            "approved_by": self.approved_by,
            "status": self.status,
        }


class ReportVerificationToken(db.Model):
    __tablename__ = "report_verification_tokens"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = db.Column(db.String(36), nullable=False, index=True)
    report_id = db.Column(db.String(36), nullable=False)
    report_code = db.Column(db.String(50), nullable=False)
    token = db.Column(db.String(128), unique=True, nullable=False, index=True)
    report_version = db.Column(db.Integer, nullable=False)
    report_hash = db.Column(db.String(128))
    status = db.Column(db.String(30), default="ACTIVE")
    expires_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    revoked_at = db.Column(db.DateTime)

    def to_dict(self) -> dict:
        return {
            "report_code": self.report_code,
            "report_version": self.report_version,
            "status": self.status,
            "verified": self.status == "ACTIVE",
        }


class CriticalValueAcknowledgement(db.Model):
    __tablename__ = "critical_value_acknowledgements"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = db.Column(db.String(36), nullable=False, index=True)
    alert_id = db.Column(db.String(36))
    result_item_id = db.Column(db.String(36))
    acknowledged_by = db.Column(db.String(255), nullable=False)
    acknowledged_at = db.Column(db.DateTime, default=datetime.utcnow)
    communication_method = db.Column(db.String(30), default="in_app")
    escalation_level = db.Column(db.Integer, default=0)
    resolution_note = db.Column(db.Text)
    correlation_id = db.Column(db.String(64))

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "acknowledged_by": self.acknowledged_by,
            "acknowledged_at": self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            "communication_method": self.communication_method,
        }
