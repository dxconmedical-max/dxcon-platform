"""Attachment and file storage service."""

from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timezone

from flask import current_app

from app.extensions.db import db
from app.storage.factory import get_storage_provider
from app.storage.lifecycle import apply_lifecycle
from app.storage.models import FileMetadata
from app.storage.signed_urls import generate_signed_url, verify_signed_url
from app.storage.validation import sanitize_filename, validate_download, validate_upload
from app.storage.virus_scan import get_virus_scan_provider


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class AttachmentService:
    @staticmethod
    def list_files(*, tenant_id: str | None = None, limit: int = 100):
        query = FileMetadata.query
        if tenant_id:
            query = query.filter_by(tenant_id=tenant_id)
        rows = query.order_by(FileMetadata.created_at.desc()).limit(limit).all()
        return {"count": len(rows), "files": [row.to_dict() for row in rows]}

    @staticmethod
    def upload_file(*, filename: str, content_type: str, data: bytes, tenant_id: str | None = None):
        app = current_app._get_current_object()
        validation = validate_upload(
            filename,
            content_type,
            len(data),
            max_size_bytes=int(app.config.get("FILE_MAX_SIZE_BYTES", 10 * 1024 * 1024)),
        )
        if not validation["ok"]:
            raise ValueError("; ".join(validation["errors"]))

        scan = get_virus_scan_provider().scan(
            filename=validation["filename"],
            content_type=content_type,
            data=data,
        )
        if not scan.get("clean", False):
            raise ValueError("virus scan failed")

        file_id = str(uuid.uuid4())
        storage_key = f"{tenant_id or 'global'}/{file_id}/{validation['filename']}"
        provider = get_storage_provider(app)
        stored = provider.put(storage_key, data, content_type)
        checksum = hashlib.sha256(data).hexdigest()
        now = _utc_now()
        metadata = FileMetadata(
            id=file_id,
            tenant_id=tenant_id,
            filename=validation["filename"],
            content_type=content_type,
            size_bytes=stored.size_bytes,
            storage_provider=provider.name,
            storage_key=storage_key,
            checksum_sha256=checksum,
            status="ACTIVE",
            virus_scan_status=scan.get("status", "SKIPPED"),
            created_at=now,
            updated_at=now,
        )
        apply_lifecycle(metadata, retention_days=int(app.config.get("FILE_RETENTION_DAYS", 365)))
        db.session.add(metadata)
        db.session.commit()
        return metadata.to_dict()

    @staticmethod
    def get_file(file_id: str):
        row = FileMetadata.query.get(file_id)
        if not row:
            return None
        return row.to_dict()

    @staticmethod
    def download_file(file_id: str, *, token: str | None = None, expires: int | None = None):
        row = FileMetadata.query.get(file_id)
        if not row:
            return None
        validation = validate_download(row.status)
        if not validation["ok"]:
            raise ValueError(validation["error"])

        app = current_app._get_current_object()
        if token is not None and expires is not None:
            if not verify_signed_url(file_id, token, int(expires), secret=app.config["SECRET_KEY"]):
                raise PermissionError("invalid or expired signed URL")
        provider = get_storage_provider(app)
        data = provider.get(row.storage_key)
        digest = hashlib.sha256(data).hexdigest()
        if digest != row.checksum_sha256:
            raise ValueError("checksum mismatch")
        return {"metadata": row.to_dict(), "data": data}

    @staticmethod
    def create_signed_url(file_id: str):
        app = current_app._get_current_object()
        row = FileMetadata.query.get(file_id)
        if not row:
            return None
        signed = generate_signed_url(
            file_id,
            secret=app.config["SECRET_KEY"],
            ttl_seconds=int(app.config.get("SIGNED_URL_TTL_SECONDS", 3600)),
        )
        return {"file": row.to_dict(), "signed_url": signed}

    @staticmethod
    def attach_to_record(file_id: str, *, object_type: str, object_id: str):
        metadata = AttachmentService.get_file(file_id)
        if not metadata:
            raise ValueError("file not found")
        return {
            "attachment": {
                "file_id": file_id,
                "object_type": object_type,
                "object_id": object_id,
                "filename": metadata["filename"],
            }
        }
