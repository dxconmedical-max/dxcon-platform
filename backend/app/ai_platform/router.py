from typing import Optional

from app.ai_platform.registry import AIProviderRegistry


class ModelRouter:
    DEFAULT_ROUTES = {
        "interpretation": "LOCAL",
        "summary": "LOCAL",
        "risk": "LOCAL",
        "general": "LOCAL",
    }

    @classmethod
    def resolve(cls, task_type: str, preferred_provider_type: Optional[str] = None) -> str:
        if preferred_provider_type:
            provider_type = preferred_provider_type.upper()
            if provider_type in AIProviderRegistry.list_types():
                return provider_type
        return cls.DEFAULT_ROUTES.get((task_type or "general").lower(), "LOCAL")

    @classmethod
    def route(cls, task_type: str, preferred_provider_type: Optional[str] = None):
        provider_type = cls.resolve(task_type, preferred_provider_type)
        provider = AIProviderRegistry.get_instance(provider_type)
        return {"provider_type": provider_type, "provider": provider}
