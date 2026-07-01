from datetime import datetime
import uuid

from app.extensions.db import db


class StandardCodeSystem(db.Model):
    __tablename__ = "standard_code_systems"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    system_code = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(255), nullable=False)
    version = db.Column(db.String(50))
    status = db.Column(db.String(50), default="ACTIVE")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "system_code": self.system_code,
            "name": self.name,
            "version": self.version,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class StandardCode(db.Model):
    __tablename__ = "standard_codes"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    system_id = db.Column(db.String(36), db.ForeignKey("standard_code_systems.id"), nullable=False)
    code = db.Column(db.String(100), nullable=False, index=True)
    display = db.Column(db.String(500))
    category = db.Column(db.String(100))
    status = db.Column(db.String(50), default="ACTIVE")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint("system_id", "code", name="uq_standard_code_system_code"),)

    def to_dict(self):
        return {
            "id": self.id,
            "system_id": self.system_id,
            "code": self.code,
            "display": self.display,
            "category": self.category,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class StandardMapping(db.Model):
    __tablename__ = "standard_mappings"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    mapping_code = db.Column(db.String(50), unique=True, nullable=False)
    source_type = db.Column(db.String(100), nullable=False)
    source_code = db.Column(db.String(100), nullable=False)
    target_system = db.Column(db.String(50), nullable=False)
    target_code = db.Column(db.String(100), nullable=False)
    target_display = db.Column(db.String(500))
    status = db.Column(db.String(50), default="ACTIVE")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "mapping_code": self.mapping_code,
            "source_type": self.source_type,
            "source_code": self.source_code,
            "target_system": self.target_system,
            "target_code": self.target_code,
            "target_display": self.target_display,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class StandardValidationLog(db.Model):
    __tablename__ = "standard_validation_logs"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    standard_type = db.Column(db.String(50), nullable=False)
    resource_type = db.Column(db.String(100))
    status = db.Column(db.String(50), default="VALID")
    detail_json = db.Column(db.Text, default="{}")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "standard_type": self.standard_type,
            "resource_type": self.resource_type,
            "status": self.status,
            "detail_json": self.detail_json,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class StandardImportBatch(db.Model):
    __tablename__ = "standard_import_batches"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    batch_code = db.Column(db.String(50), unique=True, nullable=False)
    system_code = db.Column(db.String(50), nullable=False)
    record_count = db.Column(db.Integer, default=0)
    status = db.Column(db.String(50), default="COMPLETED")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "batch_code": self.batch_code,
            "system_code": self.system_code,
            "record_count": self.record_count,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class DICOMStudyMetadata(db.Model):
    __tablename__ = "dicom_study_metadata"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    study_uid = db.Column(db.String(255), unique=True, nullable=False)
    patient_id = db.Column(db.String(100))
    accession_number = db.Column(db.String(100))
    study_date = db.Column(db.String(20))
    modality = db.Column(db.String(20))
    description = db.Column(db.String(500))
    metadata_json = db.Column(db.Text, default="{}")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "study_uid": self.study_uid,
            "patient_id": self.patient_id,
            "accession_number": self.accession_number,
            "study_date": self.study_date,
            "modality": self.modality,
            "description": self.description,
            "metadata_json": self.metadata_json,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class DICOMSeriesMetadata(db.Model):
    __tablename__ = "dicom_series_metadata"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    study_id = db.Column(db.String(36), db.ForeignKey("dicom_study_metadata.id"), nullable=False)
    series_uid = db.Column(db.String(255), unique=True, nullable=False)
    series_number = db.Column(db.String(20))
    modality = db.Column(db.String(20))
    body_part = db.Column(db.String(100))
    metadata_json = db.Column(db.Text, default="{}")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "study_id": self.study_id,
            "series_uid": self.series_uid,
            "series_number": self.series_number,
            "modality": self.modality,
            "body_part": self.body_part,
            "metadata_json": self.metadata_json,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class DICOMInstanceMetadata(db.Model):
    __tablename__ = "dicom_instance_metadata"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    series_id = db.Column(db.String(36), db.ForeignKey("dicom_series_metadata.id"), nullable=False)
    sop_instance_uid = db.Column(db.String(255), unique=True, nullable=False)
    instance_number = db.Column(db.String(20))
    transfer_syntax = db.Column(db.String(100))
    metadata_json = db.Column(db.Text, default="{}")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "series_id": self.series_id,
            "sop_instance_uid": self.sop_instance_uid,
            "instance_number": self.instance_number,
            "transfer_syntax": self.transfer_syntax,
            "metadata_json": self.metadata_json,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
