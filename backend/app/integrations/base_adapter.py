from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class BaseAdapter(ABC):
    adapter_type: str = "base"

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.connected = False

    @abstractmethod
    def connect(self) -> Dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def disconnect(self) -> Dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def health_check(self) -> Dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def send(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def receive(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def transform(self, payload: Dict[str, Any], direction: str = "outbound") -> Dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def validate(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError


class DemoAdapter(BaseAdapter):
    """Safe demo adapter base — no external vendor calls."""

    vendor_label: str = "Demo"

    def connect(self) -> Dict[str, Any]:
        self.connected = True
        return {"status": "CONNECTED", "adapter": self.adapter_type, "vendor": self.vendor_label}

    def disconnect(self) -> Dict[str, Any]:
        self.connected = False
        return {"status": "DISCONNECTED", "adapter": self.adapter_type}

    def health_check(self) -> Dict[str, Any]:
        return {
            "status": "OK" if self.connected else "DEGRADED",
            "adapter": self.adapter_type,
            "connected": self.connected,
        }

    def send(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        transformed = self.transform(payload, direction="outbound")
        validation = self.validate(transformed)
        if not validation.get("valid"):
            return {"status": "REJECTED", "errors": validation.get("errors", [])}
        return {"status": "ACCEPTED", "adapter": self.adapter_type, "payload": transformed}

    def receive(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        validation = self.validate(payload)
        if not validation.get("valid"):
            return {"status": "REJECTED", "errors": validation.get("errors", [])}
        return {
            "status": "RECEIVED",
            "adapter": self.adapter_type,
            "payload": self.transform(payload, direction="inbound"),
        }

    def transform(self, payload: Dict[str, Any], direction: str = "outbound") -> Dict[str, Any]:
        return {
            "adapter": self.adapter_type,
            "direction": direction,
            "data": payload,
            "vendor": self.vendor_label,
        }

    def validate(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        if payload is None:
            return {"valid": False, "errors": ["payload is required"]}
        return {"valid": True, "errors": []}
