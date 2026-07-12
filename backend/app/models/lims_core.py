"""Release 7.0 — LIMS Core specimen, barcode, accession, and storage models."""

from __future__ import annotations

from datetime import datetime
import uuid

from app.core.statuses import LIMS_SPECIMEN_CREATED, LIMS_CONTAINER_TYPES
from app.extensions.db import db


class LimsSpecimen(db.Model):
    __tablename__ = "specimens"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    barcode = db.Column(db.String(50), unique=True, nullable=False, index=True)
    human_readable = db.Column(db.String(50), unique=True, nullable=False, index=True)
    order_id = db.Column(db.String(36), index=True)
    order_code = db.Column(db.String(50), index=True)
    patient_code = db.Column(db.String(50), index=True)
    organization_id = db.Column(db.String(36), index=True)
    status = db.Column(db.String(30), nullable=False, default=LIMS_SPECIMEN_CREATED, index=True)
    container_type = db.Column(db.String(30))
    volume = db.Column(db.Float)
    volume_unit = db.Column(db.String(20), default="mL")
    collected_at = db.Column(db.DateTime)
    expires_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "barcode": self.barcode,
            "human_readable": self.human_readable,
            "order_id": self.order_id,
            "order_code": self.order_code,
            "patient_code": self.patient_code,
            "organization_id": self.organization_id,
            "status": self.status,
            "container_type": self.container_type,
            "volume": self.volume,
            "volume_unit": self.volume_unit,
            "collected_at": self.collected_at.isoformat() if self.collected_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class LimsContainer(db.Model):
    __tablename__ = "containers"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    container_code = db.Column(db.String(50), unique=True, nullable=False, index=True)
    container_type = db.Column(db.String(30), nullable=False)
    volume_capacity = db.Column(db.Float)
    volume_unit = db.Column(db.String(20), default="mL")
    specimen_id = db.Column(db.String(36), db.ForeignKey("specimens.id"), index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "container_code": self.container_code,
            "container_type": self.container_type,
            "volume_capacity": self.volume_capacity,
            "volume_unit": self.volume_unit,
            "specimen_id": self.specimen_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class LimsBarcodeLog(db.Model):
    __tablename__ = "barcode_logs"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    barcode_value = db.Column(db.String(100), unique=True, nullable=False, index=True)
    human_readable = db.Column(db.String(50), nullable=False, index=True)
    format = db.Column(db.String(20), nullable=False, default="CODE128")
    specimen_id = db.Column(db.String(36), db.ForeignKey("specimens.id"), index=True)
    generated_by = db.Column(db.String(255))
    generated_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "barcode_value": self.barcode_value,
            "human_readable": self.human_readable,
            "format": self.format,
            "specimen_id": self.specimen_id,
            "generated_by": self.generated_by,
            "generated_at": self.generated_at.isoformat() if self.generated_at else None,
        }


class LimsStorageLocation(db.Model):
    __tablename__ = "storage_locations"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    location_code = db.Column(db.String(50), unique=True, nullable=False, index=True)
    rack = db.Column(db.String(50))
    shelf = db.Column(db.String(50))
    batch = db.Column(db.String(50))
    laboratory_id = db.Column(db.String(36), index=True)
    status = db.Column(db.String(30), default="active")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "location_code": self.location_code,
            "rack": self.rack,
            "shelf": self.shelf,
            "batch": self.batch,
            "laboratory_id": self.laboratory_id,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class LimsAccession(db.Model):
    __tablename__ = "accessions"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    accession_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    specimen_id = db.Column(db.String(36), db.ForeignKey("specimens.id"), nullable=False, index=True)
    storage_location_id = db.Column(db.String(36), db.ForeignKey("storage_locations.id"))
    rack = db.Column(db.String(50))
    shelf = db.Column(db.String(50))
    batch = db.Column(db.String(50))
    operator = db.Column(db.String(255))
    accessioned_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(30), default="active")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "accession_number": self.accession_number,
            "specimen_id": self.specimen_id,
            "storage_location_id": self.storage_location_id,
            "rack": self.rack,
            "shelf": self.shelf,
            "batch": self.batch,
            "operator": self.operator,
            "accessioned_at": self.accessioned_at.isoformat() if self.accessioned_at else None,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class LimsSampleStatusHistory(db.Model):
    __tablename__ = "sample_status_history"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    specimen_id = db.Column(db.String(36), db.ForeignKey("specimens.id"), nullable=False, index=True)
    from_status = db.Column(db.String(30))
    to_status = db.Column(db.String(30), nullable=False)
    actor = db.Column(db.String(255))
    note = db.Column(db.Text)
    transitioned_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "specimen_id": self.specimen_id,
            "from_status": self.from_status,
            "to_status": self.to_status,
            "actor": self.actor,
            "note": self.note,
            "transitioned_at": self.transitioned_at.isoformat() if self.transitioned_at else None,
        }


VALID_LIMS_CONTAINER_TYPES = LIMS_CONTAINER_TYPES
