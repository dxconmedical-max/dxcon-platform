"""Pluggable analyzer adapter interfaces — vendor logic isolated here."""

from __future__ import annotations

import os
from abc import ABC, abstractmethod
from typing import Any


class AnalyzerAdapter(ABC):
    protocol: str = "BASE"

    @abstractmethod
    def connect(self) -> dict[str, Any]: ...

    @abstractmethod
    def disconnect(self) -> dict[str, Any]: ...

    @abstractmethod
    def health_check(self) -> dict[str, Any]: ...

    def query_orders(self) -> dict[str, Any]:
        return {"orders": [], "mode": "unidirectional"}

    def send_worklist(self, items: list[dict]) -> dict[str, Any]:
        return {"sent": len(items), "acknowledged": False}

    @abstractmethod
    def parse_result(self, raw: dict[str, Any]) -> dict[str, Any]: ...

    def acknowledge(self, message_id: str) -> dict[str, Any]:
        return {"acknowledged": message_id}


class SimulatorAdapter(AnalyzerAdapter):
    protocol = "SIMULATOR"

    def connect(self) -> dict[str, Any]:
        if os.environ.get("FLASK_ENV") == "production" and os.environ.get("ANALYZER_SIMULATOR_ENABLED") != "true":
            raise PermissionError("Simulator disabled in production")
        return {"status": "SIMULATED", "connected": True}

    def disconnect(self) -> dict[str, Any]:
        return {"connected": False}

    def health_check(self) -> dict[str, Any]:
        return {"status": "SIMULATED", "healthy": True}

    def parse_result(self, raw: dict[str, Any]) -> dict[str, Any]:
        return {
            "specimen_barcode": raw.get("specimen_barcode") or raw.get("barcode"),
            "analyzer_test_code": raw.get("analyzer_test_code") or raw.get("test_code"),
            "value": raw.get("value"),
            "unit": raw.get("unit"),
            "flag": raw.get("flag"),
            "simulated": True,
        }


class ASTMAdapter(AnalyzerAdapter):
    protocol = "ASTM"

    def connect(self) -> dict[str, Any]:
        return {"status": "NOT_IMPLEMENTED", "connected": False}

    def disconnect(self) -> dict[str, Any]:
        return {"connected": False}

    def health_check(self) -> dict[str, Any]:
        return {"status": "NOT_IMPLEMENTED", "healthy": False}

    def parse_result(self, raw: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError("ASTM adapter requires on-prem gateway deployment")


ADAPTER_REGISTRY: dict[str, type[AnalyzerAdapter]] = {
    "SIMULATOR": SimulatorAdapter,
    "ASTM": ASTMAdapter,
}


def get_adapter(protocol: str) -> AnalyzerAdapter:
    cls = ADAPTER_REGISTRY.get(protocol.upper(), SimulatorAdapter)
    return cls()
