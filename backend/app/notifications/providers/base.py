from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseNotificationProvider(ABC):
    channel: str = "BASE"
    provider_code: str = "BASE"

    @abstractmethod
    def send(self, recipient: str, subject: str, body: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def validate(self, recipient: str) -> Dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def health_check(self) -> Dict[str, Any]:
        raise NotImplementedError

    def retry(self, recipient: str, subject: str, body: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        return self.send(recipient, subject, body, metadata)
