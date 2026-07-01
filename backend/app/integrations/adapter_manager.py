from typing import Any, Dict, Optional

from app.integrations.adapter_loader import load_adapters
from app.integrations.adapter_registry import AdapterRegistry


class AdapterManager:
    _initialized = False

    @classmethod
    def initialize(cls) -> dict:
        if not cls._initialized:
            load_adapters()
            cls._initialized = True
        return {"types": AdapterRegistry.list_types(), "count": len(AdapterRegistry.list_types())}

    @classmethod
    def list_adapters(cls):
        cls.initialize()
        items = []
        for adapter_type in AdapterRegistry.list_types():
            adapter = AdapterRegistry.get_instance(adapter_type)
            items.append(
                {
                    "type": adapter_type,
                    "connected": adapter.connected,
                    "vendor": getattr(adapter, "vendor_label", adapter.adapter_type),
                }
            )
        return {"count": len(items), "adapters": items}

    @classmethod
    def connect(cls, adapter_type: str, config: Optional[Dict[str, Any]] = None):
        cls.initialize()
        adapter = AdapterRegistry.get_instance(adapter_type, config)
        return adapter.connect()

    @classmethod
    def disconnect(cls, adapter_type: str):
        cls.initialize()
        return AdapterRegistry.get_instance(adapter_type).disconnect()

    @classmethod
    def health_check(cls, adapter_type: str):
        cls.initialize()
        return AdapterRegistry.get_instance(adapter_type).health_check()

    @classmethod
    def send(cls, adapter_type: str, payload: Dict[str, Any]):
        cls.initialize()
        return AdapterRegistry.get_instance(adapter_type).send(payload)

    @classmethod
    def receive(cls, adapter_type: str, payload: Dict[str, Any]):
        cls.initialize()
        return AdapterRegistry.get_instance(adapter_type).receive(payload)

    @classmethod
    def transform(cls, adapter_type: str, payload: Dict[str, Any], direction: str = "outbound"):
        cls.initialize()
        return AdapterRegistry.get_instance(adapter_type).transform(payload, direction=direction)

    @classmethod
    def validate(cls, adapter_type: str, payload: Dict[str, Any]):
        cls.initialize()
        return AdapterRegistry.get_instance(adapter_type).validate(payload)
