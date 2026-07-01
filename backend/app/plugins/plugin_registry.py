from typing import Dict, Optional, Type

from app.plugins.plugin_base import DemoPlugin, PluginBase
from app.plugins.plugin_manifest import PluginManifest


class PluginRegistry:
    _manifests: Dict[str, PluginManifest] = {}
    _classes: Dict[str, Type[PluginBase]] = {}
    _instances: Dict[str, PluginBase] = {}

    @classmethod
    def register(cls, manifest: PluginManifest, plugin_class: Type[PluginBase]) -> None:
        cls._manifests[manifest.plugin_id] = manifest
        cls._classes[manifest.plugin_id] = plugin_class

    @classmethod
    def list_manifests(cls):
        return [manifest.to_dict() for manifest in cls._manifests.values()]

    @classmethod
    def get_manifest(cls, plugin_id: str) -> Optional[PluginManifest]:
        return cls._manifests.get(plugin_id)

    @classmethod
    def get_instance(cls, plugin_id: str, config: Optional[dict] = None) -> PluginBase:
        if plugin_id not in cls._instances:
            plugin_class = cls._classes.get(plugin_id)
            if plugin_class is None:
                raise KeyError(f"Unknown plugin: {plugin_id}")
            manifest = cls._manifests[plugin_id]
            instance = plugin_class(config or {})
            instance.plugin_id = manifest.plugin_id
            instance.name = manifest.name
            instance.version = manifest.version
            cls._instances[plugin_id] = instance
        return cls._instances[plugin_id]

    @classmethod
    def reset(cls) -> None:
        cls._instances.clear()


def _build_demo_plugin_class(manifest: PluginManifest) -> Type[DemoPlugin]:
    class _Plugin(DemoPlugin):
        plugin_id = manifest.plugin_id
        name = manifest.name
        version = manifest.version

    _Plugin.__name__ = f"{manifest.plugin_id.title().replace('-', '')}Plugin"
    return _Plugin
