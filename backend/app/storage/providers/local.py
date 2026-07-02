"""Local filesystem storage provider."""

from __future__ import annotations

from pathlib import Path

from app.storage.providers.base import StorageProvider, StoredObject


class LocalStorageProvider(StorageProvider):
    name = "local"

    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        safe_key = key.replace("..", "").lstrip("/")
        return self.base_path / safe_key

    def put(self, key: str, data: bytes, content_type: str) -> StoredObject:
        path = self._path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return StoredObject(key=key, size_bytes=len(data), content_type=content_type, provider=self.name)

    def get(self, key: str) -> bytes:
        return self._path(key).read_bytes()

    def delete(self, key: str) -> bool:
        path = self._path(key)
        if not path.exists():
            return False
        path.unlink()
        return True

    def exists(self, key: str) -> bool:
        return self._path(key).exists()

    def validate_config(self) -> dict:
        writable = self.base_path.exists() and self.base_path.is_dir()
        try:
            probe = self.base_path / ".dxcon-storage-probe"
            probe.write_text("ok", encoding="utf-8")
            probe.unlink(missing_ok=True)
            writable = True
        except OSError:
            writable = False
        return {"ok": writable, "path": str(self.base_path.resolve())}
