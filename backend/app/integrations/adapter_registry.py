from typing import Any, Dict, Optional, Type

from app.integrations.base_adapter import BaseAdapter


class AdapterRegistry:
    _adapters: Dict[str, Type[BaseAdapter]] = {}
    _instances: Dict[str, BaseAdapter] = {}

    @classmethod
    def register(cls, adapter_type: str, adapter_class: Type[BaseAdapter]) -> None:
        cls._adapters[adapter_type.upper()] = adapter_class

    @classmethod
    def get_class(cls, adapter_type: str) -> Optional[Type[BaseAdapter]]:
        return cls._adapters.get(adapter_type.upper())

    @classmethod
    def list_types(cls):
        return sorted(cls._adapters.keys())

    @classmethod
    def get_instance(cls, adapter_type: str, config: Optional[Dict[str, Any]] = None) -> BaseAdapter:
        key = adapter_type.upper()
        if key not in cls._instances:
            adapter_class = cls.get_class(key)
            if adapter_class is None:
                raise KeyError(f"Unknown adapter type: {adapter_type}")
            cls._instances[key] = adapter_class(config or {})
        return cls._instances[key]

    @classmethod
    def reset(cls) -> None:
        cls._instances.clear()
