import json

from app.core.statuses import INTEGRATION_PLUGIN_DISABLED, INTEGRATION_PLUGIN_ENABLED
from app.extensions.db import db
from app.models.integration_platform import IntegrationPluginState
from app.plugins.plugin_manifest import PluginManifest
from app.plugins.plugin_registry import PluginRegistry, _build_demo_plugin_class


DEFAULT_PLUGINS = (
    PluginManifest("webhook-delivery", "Webhook Delivery Plugin", "1.0.0", "Delivers signed webhook payloads"),
    PluginManifest("event-bridge", "Event Bridge Plugin", "1.0.0", "Bridges domain events to external systems"),
    PluginManifest("adapter-sync", "Adapter Sync Plugin", "1.0.0", "Synchronizes adapter health and queue jobs"),
)


class PluginManager:
    _initialized = False

    @classmethod
    def initialize(cls):
        if cls._initialized:
            return
        for manifest in DEFAULT_PLUGINS:
            PluginRegistry.register(manifest, _build_demo_plugin_class(manifest))
        cls._initialized = True

    @classmethod
    def ensure_defaults(cls):
        cls.initialize()
        for manifest in DEFAULT_PLUGINS:
            row = IntegrationPluginState.query.filter_by(plugin_id=manifest.plugin_id).first()
            if row:
                continue
            db.session.add(
                IntegrationPluginState(
                    plugin_id=manifest.plugin_id,
                    name=manifest.name,
                    version=manifest.version,
                    status=INTEGRATION_PLUGIN_ENABLED,
                    config_json=json.dumps({}),
                )
            )
        db.session.commit()
        return {"seeded": True, "count": len(DEFAULT_PLUGINS)}

    @classmethod
    def list_plugins(cls):
        cls.ensure_defaults()
        items = []
        for manifest in PluginRegistry.list_manifests():
            row = IntegrationPluginState.query.filter_by(plugin_id=manifest["plugin_id"]).first()
            items.append(
                {
                    **manifest,
                    "status": row.status if row else INTEGRATION_PLUGIN_DISABLED,
                    "enabled": row.status == INTEGRATION_PLUGIN_ENABLED if row else False,
                }
            )
        return {"count": len(items), "plugins": items}

    @classmethod
    def get_plugin(cls, plugin_id: str):
        cls.ensure_defaults()
        manifest = PluginRegistry.get_manifest(plugin_id)
        if manifest is None:
            raise KeyError(plugin_id)
        row = IntegrationPluginState.query.filter_by(plugin_id=plugin_id).first()
        instance = PluginRegistry.get_instance(plugin_id, json.loads(row.config_json or "{}") if row else {})
        return {
            **manifest.to_dict(),
            "status": row.status if row else INTEGRATION_PLUGIN_DISABLED,
            "enabled": row.status == INTEGRATION_PLUGIN_ENABLED if row else False,
            "config": json.loads(row.config_json or "{}") if row else {},
            "health": instance.health_check(),
        }

    @classmethod
    def enable(cls, plugin_id: str, config: dict = None):
        cls.ensure_defaults()
        row = IntegrationPluginState.query.filter_by(plugin_id=plugin_id).first()
        if row is None:
            raise KeyError(plugin_id)
        if config is not None:
            manifest = PluginRegistry.get_manifest(plugin_id)
            validation = manifest.validate_config(config)
            if not validation["valid"]:
                return validation
            row.config_json = json.dumps(config)
        instance = PluginRegistry.get_instance(plugin_id, json.loads(row.config_json or "{}"))
        result = instance.on_enable()
        row.status = INTEGRATION_PLUGIN_ENABLED
        db.session.commit()
        return {"plugin_id": plugin_id, "status": INTEGRATION_PLUGIN_ENABLED, "result": result}

    @classmethod
    def disable(cls, plugin_id: str):
        cls.ensure_defaults()
        row = IntegrationPluginState.query.filter_by(plugin_id=plugin_id).first()
        if row is None:
            raise KeyError(plugin_id)
        instance = PluginRegistry.get_instance(plugin_id, json.loads(row.config_json or "{}"))
        result = instance.on_disable()
        row.status = INTEGRATION_PLUGIN_DISABLED
        db.session.commit()
        return {"plugin_id": plugin_id, "status": INTEGRATION_PLUGIN_DISABLED, "result": result}

    @classmethod
    def validate_config(cls, plugin_id: str, config: dict):
        manifest = PluginRegistry.get_manifest(plugin_id)
        if manifest is None:
            raise KeyError(plugin_id)
        manifest_validation = manifest.validate_config(config)
        instance = PluginRegistry.get_instance(plugin_id, config)
        plugin_validation = instance.validate_config(config)
        errors = manifest_validation.get("errors", []) + plugin_validation.get("errors", [])
        return {"valid": not errors, "errors": errors}

    @classmethod
    def health_check(cls, plugin_id: str):
        cls.ensure_defaults()
        if IntegrationPluginState.query.filter_by(plugin_id=plugin_id).first() is None:
            raise KeyError(plugin_id)
        instance = PluginRegistry.get_instance(plugin_id)
        return instance.health_check()
