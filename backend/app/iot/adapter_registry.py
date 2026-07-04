from typing import Any, Dict, Optional, Type

from app.iot.base_adapter import BaseIoTDeviceAdapter


class IoTAdapterRegistry:
    _adapters: Dict[str, Type[BaseIoTDeviceAdapter]] = {}
    _instances: Dict[str, BaseIoTDeviceAdapter] = {}

    @classmethod
    def register(cls, adapter_type: str, adapter_class: Type[BaseIoTDeviceAdapter]) -> None:
        cls._adapters[adapter_type.upper()] = adapter_class

    @classmethod
    def list_types(cls):
        return sorted(cls._adapters.keys())

    @classmethod
    def get_instance(cls, adapter_type: str, config: Optional[Dict[str, Any]] = None) -> BaseIoTDeviceAdapter:
        key = (adapter_type or "GENERIC").upper()
        if key not in cls._instances:
            adapter_class = cls._adapters.get(key)
            if adapter_class is None:
                raise KeyError(f"Unknown IoT adapter type: {adapter_type}")
            cls._instances[key] = adapter_class()
        return cls._instances[key]

    @classmethod
    def reset(cls) -> None:
        cls._instances.clear()
