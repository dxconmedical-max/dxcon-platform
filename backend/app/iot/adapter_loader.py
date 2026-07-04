from app.iot.adapter_registry import IoTAdapterRegistry
from app.iot.adapters import ADAPTER_CLASSES


def load_iot_adapters() -> dict:
    for adapter_type, adapter_class in ADAPTER_CLASSES.items():
        IoTAdapterRegistry.register(adapter_type, adapter_class)
    return {"loaded": len(ADAPTER_CLASSES), "types": IoTAdapterRegistry.list_types()}
