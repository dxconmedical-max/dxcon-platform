from app.notifications.providers.base import BaseNotificationProvider
from app.notifications.providers.channels import (
    InAppProvider,
    PushProvider,
    SMSProvider,
    WebhookProvider,
    ZaloOAProvider,
)
from app.notifications.providers.email import EmailProvider


class NotificationRegistry:
    _providers = {}

    @classmethod
    def register(cls, provider: BaseNotificationProvider):
        cls._providers[provider.channel] = provider

    @classmethod
    def get(cls, channel: str) -> BaseNotificationProvider:
        if channel not in cls._providers:
            raise KeyError(f"Unknown notification channel: {channel}")
        return cls._providers[channel]

    @classmethod
    def list_providers(cls):
        return [
            {
                "channel": provider.channel,
                "provider_code": provider.provider_code,
                "health": provider.health_check(),
            }
            for provider in cls._providers.values()
        ]

    @classmethod
    def initialize(cls):
        if cls._providers:
            return
        for provider in (
            EmailProvider(),
            SMSProvider(),
            ZaloOAProvider(),
            PushProvider(),
            WebhookProvider(),
            InAppProvider(),
        ):
            cls.register(provider)
