from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class PluginBase(ABC):
    plugin_id: str = "base"
    name: str = "Base Plugin"
    version: str = "1.0.0"

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.enabled = False

    @abstractmethod
    def on_enable(self) -> Dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def on_disable(self) -> Dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def health_check(self) -> Dict[str, Any]:
        raise NotImplementedError

    def validate_config(self, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        data = config if config is not None else self.config
        if not isinstance(data, dict):
            return {"valid": False, "errors": ["config must be an object"]}
        return {"valid": True, "errors": []}


class DemoPlugin(PluginBase):
    def on_enable(self) -> Dict[str, Any]:
        self.enabled = True
        return {"status": "ENABLED", "plugin_id": self.plugin_id}

    def on_disable(self) -> Dict[str, Any]:
        self.enabled = False
        return {"status": "DISABLED", "plugin_id": self.plugin_id}

    def health_check(self) -> Dict[str, Any]:
        return {
            "status": "OK" if self.enabled else "DISABLED",
            "plugin_id": self.plugin_id,
            "version": self.version,
        }
