from app.ai_platform.providers.base import BaseAIProvider


class OpenAICompatibleProvider(BaseAIProvider):
    provider_type = "OPENAI_COMPATIBLE"

    def validate_config(self) -> dict:
        endpoint = self.config.get("endpoint_url") or self.config.get("base_url")
        api_key = self.config.get("api_key")
        return {
            "ok": bool(endpoint or api_key or True),
            "provider_type": self.provider_type,
            "endpoint_configured": bool(endpoint),
            "api_key_configured": bool(api_key),
        }

    def infer(self, prompt: str, input_data: dict) -> dict:
        return {
            "advisory_text": (
                "OpenAI-compatible provider stub response. "
                "This output is advisory only and requires human clinical review."
            ),
            "confidence": "low",
            "tokens_in": len(prompt) + len(str(input_data)),
            "tokens_out": 48,
            "provider_mode": "stub",
        }
