from app.ai_platform.providers.base import BaseAIProvider


class LocalAdvisoryProvider(BaseAIProvider):
    provider_type = "LOCAL"

    def validate_config(self) -> dict:
        return {"ok": True, "provider_type": self.provider_type}

    def infer(self, prompt: str, input_data: dict) -> dict:
        summary = input_data.get("summary") or input_data.get("text") or "sample input"
        return {
            "advisory_text": (
                f"Advisory summary for review: {summary[:500]}. "
                "This is not a diagnosis and requires human clinical review."
            ),
            "confidence": "low",
            "tokens_in": len(prompt) + len(str(input_data)),
            "tokens_out": 64,
        }
