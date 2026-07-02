import json
import uuid
from typing import Dict, Optional, Type

from app.ai_platform.models import AIProvider
from app.ai_platform.providers.base import BaseAIProvider
from app.ai_platform.providers.local import LocalAdvisoryProvider
from app.ai_platform.providers.openai_compatible import OpenAICompatibleProvider
from app.extensions.db import db


PROVIDER_CLASSES: Dict[str, Type[BaseAIProvider]] = {
    "LOCAL": LocalAdvisoryProvider,
    "OPENAI_COMPATIBLE": OpenAICompatibleProvider,
}


class AIProviderRegistry:
    _instances: Dict[str, BaseAIProvider] = {}

    @classmethod
    def list_types(cls):
        return sorted(PROVIDER_CLASSES.keys())

    @classmethod
    def get_class(cls, provider_type: str) -> Optional[Type[BaseAIProvider]]:
        return PROVIDER_CLASSES.get((provider_type or "").upper())

    @classmethod
    def get_instance(cls, provider_type: str, config: Optional[dict] = None) -> BaseAIProvider:
        key = (provider_type or "").upper()
        if key not in cls._instances:
            provider_class = cls.get_class(key)
            if provider_class is None:
                raise KeyError(f"Unknown provider type: {provider_type}")
            cls._instances[key] = provider_class(config or {})
        return cls._instances[key]

    @classmethod
    def ensure_defaults(cls):
        if AIProvider.query.first():
            return {"seeded": False}
        db.session.add(
            AIProvider(
                provider_code="AI-LOCAL",
                name="Local Advisory Provider",
                provider_type="LOCAL",
                model_name="local-advisory-v1",
                config_json=json.dumps({"mode": "advisory"}),
                status="ACTIVE",
            )
        )
        db.session.commit()
        return {"seeded": True}

    @classmethod
    def list_providers(cls):
        cls.ensure_defaults()
        rows = AIProvider.query.order_by(AIProvider.created_at.desc()).all()
        return {"count": len(rows), "providers": [row.to_dict() for row in rows]}

    @classmethod
    def register(cls, data):
        provider_type = (data.get("provider_type") or "LOCAL").upper()
        if provider_type not in PROVIDER_CLASSES:
            raise ValueError(f"Unknown provider_type: {provider_type}")
        instance = cls.get_instance(provider_type, data.get("config") or {})
        validation = instance.validate_config()
        if not validation.get("ok"):
            raise ValueError("Provider config validation failed")
        row = AIProvider(
            provider_code=data.get("provider_code") or f"AI-{uuid.uuid4().hex[:8].upper()}",
            name=data.get("name") or provider_type,
            provider_type=provider_type,
            model_name=data.get("model_name") or "default",
            config_json=json.dumps(data.get("config") or {}),
            status=data.get("status") or "ACTIVE",
        )
        db.session.add(row)
        db.session.commit()
        return row.to_dict()

    @classmethod
    def get_provider_row(cls, provider_id):
        row = AIProvider.query.filter_by(id=provider_id).first()
        if row is None:
            raise KeyError("Provider not found")
        return row

    @classmethod
    def reset(cls):
        cls._instances.clear()
