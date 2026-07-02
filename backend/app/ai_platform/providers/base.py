from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class BaseAIProvider(ABC):
    provider_type = "BASE"

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}

    @abstractmethod
    def validate_config(self) -> dict:
        raise NotImplementedError

    @abstractmethod
    def infer(self, prompt: str, input_data: dict) -> dict:
        raise NotImplementedError
