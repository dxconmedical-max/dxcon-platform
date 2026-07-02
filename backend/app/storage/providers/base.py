"""Storage provider interfaces."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class StoredObject:
    key: str
    size_bytes: int
    content_type: str
    provider: str


class StorageProvider(ABC):
    name: str = "base"

    @abstractmethod
    def put(self, key: str, data: bytes, content_type: str) -> StoredObject:
        raise NotImplementedError

    @abstractmethod
    def get(self, key: str) -> bytes:
        raise NotImplementedError

    @abstractmethod
    def delete(self, key: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    def exists(self, key: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    def validate_config(self) -> dict:
        raise NotImplementedError

    def health(self) -> dict:
        validation = self.validate_config()
        return {"provider": self.name, "ok": validation.get("ok", False), **validation}
