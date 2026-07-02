"""Virus scan provider placeholder."""

from __future__ import annotations

from abc import ABC, abstractmethod


class VirusScanProvider(ABC):
    name: str = "base"

    @abstractmethod
    def scan(self, *, filename: str, content_type: str, data: bytes) -> dict:
        raise NotImplementedError


class NoOpVirusScanProvider(VirusScanProvider):
    name = "noop"

    def scan(self, *, filename: str, content_type: str, data: bytes) -> dict:
        return {
            "provider": self.name,
            "status": "SKIPPED",
            "clean": True,
            "detail": "virus scan placeholder; configure external scanner before production",
        }


def get_virus_scan_provider() -> VirusScanProvider:
    return NoOpVirusScanProvider()
