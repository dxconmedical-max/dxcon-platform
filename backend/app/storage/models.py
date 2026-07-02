"""File storage metadata model."""

from __future__ import annotations

from app.extensions.db import db


class FileMetadata(db.Model):
    __tablename__ = "file_metadata"

    id = db.Column(db.String(36), primary_key=True)
    tenant_id = db.Column(db.String(64))
    filename = db.Column(db.String(255), nullable=False)
    content_type = db.Column(db.String(128), nullable=False, default="application/octet-stream")
    size_bytes = db.Column(db.Integer, nullable=False, default=0)
    storage_provider = db.Column(db.String(32), nullable=False, default="local")
    storage_key = db.Column(db.String(512), nullable=False)
    checksum_sha256 = db.Column(db.String(64))
    status = db.Column(db.String(32), nullable=False, default="ACTIVE")
    virus_scan_status = db.Column(db.String(32), nullable=False, default="PENDING")
    retention_until = db.Column(db.String(32))
    created_at = db.Column(db.String(32), nullable=False)
    updated_at = db.Column(db.String(32), nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "tenant_id": self.tenant_id,
            "filename": self.filename,
            "content_type": self.content_type,
            "size_bytes": self.size_bytes,
            "storage_provider": self.storage_provider,
            "storage_key": self.storage_key,
            "checksum_sha256": self.checksum_sha256,
            "status": self.status,
            "virus_scan_status": self.virus_scan_status,
            "retention_until": self.retention_until,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
