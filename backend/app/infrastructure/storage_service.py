"""Storage abstraction — Sprint 010."""

from __future__ import annotations

import os
from pathlib import Path
from typing import BinaryIO

PROVIDERS = ("local", "s3", "minio", "azure_blob")


class StorageService:
    """File storage abstraction with local default and cloud-ready extension points."""

    def __init__(self, provider: str | None = None):
        self.provider = provider or os.environ.get("STORAGE_PROVIDER", "local")
        default = os.environ.get("UPLOAD_FOLDER")
        if not default:
            default = str(Path(__file__).resolve().parents[2] / "uploads")
        self.base_path = Path(default)

    def store(self, category: str, filename: str, data: bytes | BinaryIO) -> dict:
        if self.provider == "local":
            dest_dir = self.base_path / category
            dest_dir.mkdir(parents=True, exist_ok=True)
            dest = dest_dir / filename
            if isinstance(data, bytes):
                dest.write_bytes(data)
            else:
                dest.write_bytes(data.read())
            return {"provider": "local", "path": str(dest), "url": f"/files/{category}/{filename}"}
        if self.provider in ("s3", "minio"):
            return {"provider": self.provider, "path": f"s3://{os.environ.get('S3_BUCKET', 'dxcon')}/{category}/{filename}", "ready": False}
        if self.provider == "azure_blob":
            return {"provider": "azure_blob", "path": f"azure://{category}/{filename}", "ready": False}
        raise ValueError(f"Unknown storage provider: {self.provider}")

    def resolve(self, category: str, filename: str) -> str | None:
        if self.provider == "local":
            path = self.base_path / category / filename
            return str(path) if path.exists() else None
        return None
