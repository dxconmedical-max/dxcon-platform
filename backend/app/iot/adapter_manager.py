from typing import Any, Dict

from app.iot.adapter_loader import load_iot_adapters
from app.iot.adapter_registry import IoTAdapterRegistry


class IoTAdapterManager:
    _initialized = False

    @classmethod
    def initialize(cls) -> dict:
        if not cls._initialized:
            load_iot_adapters()
            cls._initialized = True
        return {"types": IoTAdapterRegistry.list_types(), "count": len(IoTAdapterRegistry.list_types())}

    @classmethod
    def list_adapters(cls):
        cls.initialize()
        items = []
        for adapter_type in IoTAdapterRegistry.list_types():
            adapter = IoTAdapterRegistry.get_instance(adapter_type)
            items.append(
                {
                    "type": adapter_type,
                    "vendor": getattr(adapter, "vendor_label", adapter.adapter_type),
                }
            )
        return {"count": len(items), "adapters": items}

    @classmethod
    def normalize(cls, adapter_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        cls.initialize()
        return IoTAdapterRegistry.get_instance(adapter_type).ingest(payload)
