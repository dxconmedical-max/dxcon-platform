"""Analyzer integration models — Release 7.0 Sprint 5."""

from __future__ import annotations

import uuid
from datetime import datetime

from app.extensions.db import db


class AnalyzerIntegrationMessage(db.Model):
    __tablename__ = "analyzer_integration_messages"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = db.Column(db.String(36), nullable=False, index=True)
    laboratory_id = db.Column(db.String(36))
    analyzer_id = db.Column(db.String(36))
    message_type = db.Column(db.String(30), nullable=False)
    protocol = db.Column(db.String(30))
    status = db.Column(db.String(30), default="RECEIVED")
    message_hash = db.Column(db.String(64), nullable=False, unique=True, index=True)
    correlation_id = db.Column(db.String(64))
    external_message_id = db.Column(db.String(128))
    received_at = db.Column(db.DateTime, default=datetime.utcnow)
    processed_at = db.Column(db.DateTime)
    retry_count = db.Column(db.Integer, default=0)
    validation_status = db.Column(db.String(30))
    error_code = db.Column(db.String(30))
    payload_ref = db.Column(db.String(255))
    redacted_summary = db.Column(db.Text)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "organization_id": self.organization_id,
            "analyzer_id": self.analyzer_id,
            "message_type": self.message_type,
            "protocol": self.protocol,
            "status": self.status,
            "correlation_id": self.correlation_id,
            "received_at": self.received_at.isoformat() if self.received_at else None,
            "error_code": self.error_code,
            "redacted_summary": self.redacted_summary,
        }


class IntegrationTestMapping(db.Model):
    __tablename__ = "integration_test_mappings"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = db.Column(db.String(36), nullable=False, index=True)
    mapping_code = db.Column(db.String(50), unique=True, nullable=False)
    analyzer_test_code = db.Column(db.String(50), nullable=False)
    dxcon_test_code = db.Column(db.String(50), nullable=False)
    specimen_type = db.Column(db.String(50))
    unit = db.Column(db.String(30))
    decimal_precision = db.Column(db.Integer, default=2)
    loinc_code = db.Column(db.String(20))
    version = db.Column(db.Integer, default=1)
    approved_by = db.Column(db.String(255))
    effective_at = db.Column(db.DateTime)
    status = db.Column(db.String(30), default="ACTIVE")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "mapping_code": self.mapping_code,
            "analyzer_test_code": self.analyzer_test_code,
            "dxcon_test_code": self.dxcon_test_code,
            "unit": self.unit,
            "version": self.version,
            "approved_by": self.approved_by,
            "status": self.status,
        }


class IntegrationQuarantine(db.Model):
    __tablename__ = "integration_quarantine"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = db.Column(db.String(36), nullable=False, index=True)
    message_id = db.Column(db.String(36), db.ForeignKey("analyzer_integration_messages.id"))
    reason_code = db.Column(db.String(50), nullable=False)
    reason_detail = db.Column(db.Text)
    specimen_barcode = db.Column(db.String(50))
    analyzer_test_code = db.Column(db.String(50))
    original_value = db.Column(db.Text)
    normalized_value = db.Column(db.Text)
    status = db.Column(db.String(30), default="OPEN")
    reviewed_by = db.Column(db.String(255))
    reviewed_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "reason_code": self.reason_code,
            "reason_detail": self.reason_detail,
            "specimen_barcode": self.specimen_barcode,
            "status": self.status,
            "original_value": self.original_value,
        }


class AnalyzerWorklistItem(db.Model):
    __tablename__ = "analyzer_worklist_items"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = db.Column(db.String(36), nullable=False, index=True)
    analyzer_id = db.Column(db.String(36), nullable=False)
    specimen_barcode = db.Column(db.String(50))
    order_code = db.Column(db.String(50))
    test_code = db.Column(db.String(50))
    status = db.Column(db.String(30), default="QUEUED")
    sent_at = db.Column(db.DateTime)
    acknowledged_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    correlation_id = db.Column(db.String(64))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "analyzer_id": self.analyzer_id,
            "specimen_barcode": self.specimen_barcode,
            "test_code": self.test_code,
            "status": self.status,
            "correlation_id": self.correlation_id,
        }


class AnalyzerPreliminaryResult(db.Model):
    __tablename__ = "analyzer_preliminary_results"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = db.Column(db.String(36), nullable=False, index=True)
    analyzer_id = db.Column(db.String(36))
    message_id = db.Column(db.String(36), db.ForeignKey("analyzer_integration_messages.id"))
    specimen_barcode = db.Column(db.String(50))
    order_code = db.Column(db.String(50))
    test_code = db.Column(db.String(50))
    original_value = db.Column(db.Text, nullable=False)
    normalized_value = db.Column(db.Text)
    unit = db.Column(db.String(30))
    flag = db.Column(db.String(30))
    review_status = db.Column(db.String(30), default="PENDING_REVIEW")
    auto_released = db.Column(db.Boolean, default=False)
    duplicate_of = db.Column(db.String(36))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "specimen_barcode": self.specimen_barcode,
            "test_code": self.test_code,
            "original_value": self.original_value,
            "normalized_value": self.normalized_value,
            "unit": self.unit,
            "flag": self.flag,
            "review_status": self.review_status,
            "auto_released": self.auto_released,
        }
