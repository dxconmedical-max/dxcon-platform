from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class PluginManifest:
    plugin_id: str
    name: str
    version: str = "1.0.0"
    description: str = ""
    config_schema: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "plugin_id": self.plugin_id,
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "config_schema": self.config_schema,
            "dependencies": self.dependencies,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PluginManifest":
        return cls(
            plugin_id=data["plugin_id"],
            name=data.get("name") or data["plugin_id"],
            version=data.get("version") or "1.0.0",
            description=data.get("description") or "",
            config_schema=data.get("config_schema") or {},
            dependencies=data.get("dependencies") or [],
        )

    def validate_config(self, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        config = config or {}
        errors = []
        for key, spec in self.config_schema.items():
            if spec.get("required") and key not in config:
                errors.append(f"missing required config: {key}")
        return {"valid": not errors, "errors": errors}
