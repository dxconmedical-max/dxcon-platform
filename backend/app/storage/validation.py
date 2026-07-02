"""Upload and download validation helpers."""

from __future__ import annotations

import re
from pathlib import Path

ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "text/plain",
    "text/csv",
    "image/jpeg",
    "image/png",
    "application/json",
    "application/octet-stream",
}

ALLOWED_EXTENSIONS = {".pdf", ".txt", ".csv", ".jpg", ".jpeg", ".png", ".json"}


def sanitize_filename(filename: str) -> str:
    name = Path(filename or "upload.bin").name
    name = re.sub(r"[^A-Za-z0-9._-]", "_", name)
    return name or "upload.bin"


def validate_upload(filename: str, content_type: str, size_bytes: int, *, max_size_bytes: int) -> dict:
    errors = []
    safe_name = sanitize_filename(filename)
    extension = Path(safe_name).suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        errors.append(f"extension not allowed: {extension or 'none'}")
    if content_type not in ALLOWED_CONTENT_TYPES:
        errors.append(f"content type not allowed: {content_type}")
    if size_bytes <= 0:
        errors.append("empty upload")
    if size_bytes > max_size_bytes:
        errors.append(f"file exceeds max size {max_size_bytes}")
    return {"ok": not errors, "filename": safe_name, "errors": errors}


def validate_download(metadata_status: str) -> dict:
    if metadata_status != "ACTIVE":
        return {"ok": False, "error": f"file status {metadata_status} blocks download"}
    return {"ok": True}
