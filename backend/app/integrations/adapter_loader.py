from app.integrations.adapter_registry import AdapterRegistry
from app.integrations.adapters import ADAPTER_CLASSES


def load_adapters() -> dict:
    for adapter_type, adapter_class in ADAPTER_CLASSES.items():
        AdapterRegistry.register(adapter_type, adapter_class)
    return {"loaded": len(ADAPTER_CLASSES), "types": AdapterRegistry.list_types()}
