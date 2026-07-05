"""Sprint 007 — LIS integration and lab accession models."""

from __future__ import annotations

from datetime import datetime
import json
import uuid

from app.extensions.db import db

CONNECTOR_TYPES = (
    "REST_API",
    "HL7",
    "SFTP_FILE",
    "CSV_UPLOAD",
    "JSON_UPLOAD",
    "MANUAL",
)

DEFAULT_FIELD_MAPPINGS = {
    "external_patient_id": "patient_code",
    "external_order_id": "order_code",
    "external_sample_id": "sample_code",
    "external_test_code": "test_code",
    "value": "result_value",
    "unit": "unit",
    "reference_range": "reference_range",
    "flag": "abnormal_flag",
    "result_time": "result_time",
    "instrument": "instrument",
    "technician": "technician",
}


class LabAccessionRecord(db.Model):
    __tablename__ = "lab_accession_records"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    accession_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    order_id = db.Column(db.String(36), nullable=False)
    order_code = db.Column(db.String(50), nullable=False, index=True)
    sample_code = db.Column(db.String(50), index=True)
    patient_code = db.Column(db.String(50))
    accessioned_by = db.Column(db.String(255))
    accessioned_at = db.Column(db.DateTime)
    laboratory_id = db.Column(db.String(36))
    status = db.Column(db.String(30), default="active")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "accession_number": self.accession_number,
            "order_id": self.order_id,
            "order_code": self.order_code,
            "sample_code": self.sample_code,
            "patient_code": self.patient_code,
            "accessioned_by": self.accessioned_by,
            "accessioned_at": self.accessioned_at.isoformat() if self.accessioned_at else None,
            "laboratory_id": self.laboratory_id,
            "status": self.status,
        }


class LISConnector(db.Model):
    __tablename__ = "lis_connectors"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    connector_code = db.Column(db.String(50), unique=True, nullable=False, index=True)
    connector_name = db.Column(db.String(255), nullable=False)
    connector_type = db.Column(db.String(30), nullable=False, default="MANUAL")
    organization_id = db.Column(db.String(36))
    laboratory_id = db.Column(db.String(36))
    base_url = db.Column(db.String(500))
    auth_type = db.Column(db.String(30))
    username = db.Column(db.String(255))
    api_key_reference = db.Column(db.String(255))
    sftp_host = db.Column(db.String(255))
    sftp_path = db.Column(db.String(500))
    status = db.Column(db.String(30), default="active")
    last_sync_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "connector_code": self.connector_code,
            "connector_name": self.connector_name,
            "connector_type": self.connector_type,
            "organization_id": self.organization_id,
            "laboratory_id": self.laboratory_id,
            "base_url": self.base_url,
            "auth_type": self.auth_type,
            "username": self.username,
            "api_key_reference": self.api_key_reference,
            "sftp_host": self.sftp_host,
            "sftp_path": self.sftp_path,
            "status": self.status,
            "last_sync_at": self.last_sync_at.isoformat() if self.last_sync_at else None,
        }


class LISFieldMapping(db.Model):
    __tablename__ = "lis_field_mappings"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    connector_id = db.Column(db.String(36), db.ForeignKey("lis_connectors.id"), nullable=False, index=True)
    external_field = db.Column(db.String(100), nullable=False)
    dxcon_field = db.Column(db.String(100), nullable=False)
    transform_rule = db.Column(db.String(255))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "connector_id": self.connector_id,
            "external_field": self.external_field,
            "dxcon_field": self.dxcon_field,
            "transform_rule": self.transform_rule,
            "is_active": self.is_active,
        }


class LISImportBatch(db.Model):
    __tablename__ = "lis_import_batches"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    batch_code = db.Column(db.String(50), unique=True, nullable=False, index=True)
    connector_id = db.Column(db.String(36), db.ForeignKey("lis_connectors.id"))
    import_type = db.Column(db.String(30), nullable=False)
    file_name = db.Column(db.String(255))
    status = db.Column(db.String(30), default="processing")
    total_rows = db.Column(db.Integer, default=0)
    success_rows = db.Column(db.Integer, default=0)
    failed_rows = db.Column(db.Integer, default=0)
    imported_by = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "batch_code": self.batch_code,
            "connector_id": self.connector_id,
            "import_type": self.import_type,
            "file_name": self.file_name,
            "status": self.status,
            "total_rows": self.total_rows,
            "success_rows": self.success_rows,
            "failed_rows": self.failed_rows,
            "imported_by": self.imported_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class LISImportFailedRow(db.Model):
    __tablename__ = "lis_import_failed_rows"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    batch_id = db.Column(db.String(36), db.ForeignKey("lis_import_batches.id"), nullable=False, index=True)
    connector_id = db.Column(db.String(36))
    row_number = db.Column(db.Integer)
    error_reason = db.Column(db.Text, nullable=False)
    raw_payload = db.Column(db.Text)
    status = db.Column(db.String(30), default="failed")
    retried_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self) -> dict:
        preview = self.raw_payload or ""
        if len(preview) > 500:
            preview = preview[:500] + "…"
        return {
            "id": self.id,
            "batch_id": self.batch_id,
            "connector_id": self.connector_id,
            "row_number": self.row_number,
            "error_reason": self.error_reason,
            "raw_payload_preview": preview,
            "status": self.status,
            "retried_at": self.retried_at.isoformat() if self.retried_at else None,
        }
