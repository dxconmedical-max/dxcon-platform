"""Master Data Management — golden records and import staging."""

from __future__ import annotations

from datetime import datetime
import json
import uuid

from app.extensions.db import db

MDM_ACTIVE = "active"
MDM_INACTIVE = "inactive"
MDM_DRAFT = "draft"

IMPORT_PENDING = "pending"
IMPORT_VALIDATED = "validated"
IMPORT_APPROVED = "approved"
IMPORT_COMMITTED = "committed"
IMPORT_ROLLED_BACK = "rolled_back"
IMPORT_FAILED = "failed"

ROW_VALID = "valid"
ROW_DUPLICATE = "duplicate"
ROW_ERROR = "error"
ROW_COMMITTED = "committed"
ROW_SKIPPED = "skipped"


class MdmMasterRecord(db.Model):
    """Single source of truth for all master data entity types."""

    __tablename__ = "mdm_master_records"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    entity_type = db.Column(db.String(50), nullable=False, index=True)
    code = db.Column(db.String(100), nullable=False, index=True)
    name = db.Column(db.String(500), nullable=False)
    status = db.Column(db.String(20), default=MDM_ACTIVE, nullable=False, index=True)
    attributes_json = db.Column(db.Text, default="{}")
    parent_code = db.Column(db.String(100))
    tenant_id = db.Column(db.String(36))
    source = db.Column(db.String(50), default="mdm")
    external_id = db.Column(db.String(100))
    import_batch_id = db.Column(db.String(36), db.ForeignKey("mdm_import_batches.id"))
    created_by = db.Column(db.String(255))
    updated_by = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint("entity_type", "code", name="uq_mdm_entity_code"),
    )

    def attributes(self) -> dict:
        try:
            return json.loads(self.attributes_json or "{}")
        except json.JSONDecodeError:
            return {}

    def set_attributes(self, data: dict) -> None:
        self.attributes_json = json.dumps(data or {}, default=str)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "entity_type": self.entity_type,
            "code": self.code,
            "name": self.name,
            "status": self.status,
            "attributes": self.attributes(),
            "parent_code": self.parent_code,
            "tenant_id": self.tenant_id,
            "source": self.source,
            "external_id": self.external_id,
            "import_batch_id": self.import_batch_id,
            "created_by": self.created_by,
            "updated_by": self.updated_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class MdmImportBatch(db.Model):
    __tablename__ = "mdm_import_batches"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    batch_code = db.Column(db.String(50), unique=True, nullable=False)
    entity_type = db.Column(db.String(50), nullable=False, index=True)
    file_name = db.Column(db.String(255))
    file_format = db.Column(db.String(20))
    total_rows = db.Column(db.Integer, default=0)
    valid_rows = db.Column(db.Integer, default=0)
    duplicate_rows = db.Column(db.Integer, default=0)
    error_rows = db.Column(db.Integer, default=0)
    committed_rows = db.Column(db.Integer, default=0)
    status = db.Column(db.String(30), default=IMPORT_PENDING, nullable=False, index=True)
    preview_json = db.Column(db.Text, default="{}")
    error_summary = db.Column(db.Text)
    approved_by = db.Column(db.String(255))
    approved_at = db.Column(db.DateTime)
    committed_by = db.Column(db.String(255))
    committed_at = db.Column(db.DateTime)
    rolled_back_by = db.Column(db.String(255))
    rolled_back_at = db.Column(db.DateTime)
    created_by = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    rows = db.relationship("MdmImportRow", backref="batch", lazy=True, cascade="all, delete-orphan")

    def preview(self) -> dict:
        try:
            return json.loads(self.preview_json or "{}")
        except json.JSONDecodeError:
            return {}

    def set_preview(self, data: dict) -> None:
        self.preview_json = json.dumps(data or {}, default=str)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "batch_code": self.batch_code,
            "entity_type": self.entity_type,
            "file_name": self.file_name,
            "file_format": self.file_format,
            "total_rows": self.total_rows,
            "valid_rows": self.valid_rows,
            "duplicate_rows": self.duplicate_rows,
            "error_rows": self.error_rows,
            "committed_rows": self.committed_rows,
            "status": self.status,
            "preview": self.preview(),
            "error_summary": self.error_summary,
            "approved_by": self.approved_by,
            "approved_at": self.approved_at.isoformat() if self.approved_at else None,
            "committed_by": self.committed_by,
            "committed_at": self.committed_at.isoformat() if self.committed_at else None,
            "rolled_back_by": self.rolled_back_by,
            "rolled_back_at": self.rolled_back_at.isoformat() if self.rolled_back_at else None,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class MdmImportRow(db.Model):
    __tablename__ = "mdm_import_rows"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    batch_id = db.Column(db.String(36), db.ForeignKey("mdm_import_batches.id"), nullable=False, index=True)
    row_number = db.Column(db.Integer, nullable=False)
    code = db.Column(db.String(100))
    name = db.Column(db.String(500))
    status = db.Column(db.String(20), default=ROW_VALID, nullable=False)
    payload_json = db.Column(db.Text, default="{}")
    validation_errors = db.Column(db.Text)
    master_record_id = db.Column(db.String(36), db.ForeignKey("mdm_master_records.id"))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def payload(self) -> dict:
        try:
            return json.loads(self.payload_json or "{}")
        except json.JSONDecodeError:
            return {}

    def set_payload(self, data: dict) -> None:
        self.payload_json = json.dumps(data or {}, default=str)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "batch_id": self.batch_id,
            "row_number": self.row_number,
            "code": self.code,
            "name": self.name,
            "status": self.status,
            "payload": self.payload(),
            "validation_errors": self.validation_errors,
            "master_record_id": self.master_record_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
