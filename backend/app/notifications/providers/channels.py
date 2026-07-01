import uuid

from app.notifications.providers.base import BaseNotificationProvider


class SMSProvider(BaseNotificationProvider):
    channel = "SMS"
    provider_code = "SMS_DEMO"

    def validate(self, recipient: str):
        if not recipient or len(recipient) < 8:
            return {"valid": False, "errors": ["Invalid phone number"]}
        return {"valid": True, "errors": []}

    def health_check(self):
        return {"status": "OK", "mode": "demo", "provider": self.provider_code}

    def send(self, recipient, subject, body, metadata=None):
        validation = self.validate(recipient)
        if not validation["valid"]:
            return {"success": False, "error": validation["errors"][0]}
        return {
            "success": True,
            "mode": "demo",
            "provider_message_id": f"SMS-{uuid.uuid4().hex[:10].upper()}",
            "channel": self.channel,
            "to": recipient,
        }


class ZaloOAProvider(BaseNotificationProvider):
    channel = "ZALO"
    provider_code = "ZALO_DEMO"

    def validate(self, recipient: str):
        if not recipient:
            return {"valid": False, "errors": ["Missing Zalo recipient"]}
        return {"valid": True, "errors": []}

    def health_check(self):
        return {"status": "OK", "mode": "demo", "provider": self.provider_code}

    def send(self, recipient, subject, body, metadata=None):
        validation = self.validate(recipient)
        if not validation["valid"]:
            return {"success": False, "error": validation["errors"][0]}
        return {
            "success": True,
            "mode": "demo",
            "provider_message_id": f"ZALO-{uuid.uuid4().hex[:10].upper()}",
            "channel": self.channel,
            "to": recipient,
        }


class PushProvider(BaseNotificationProvider):
    channel = "PUSH"
    provider_code = "PUSH_DEMO"

    def validate(self, recipient: str):
        if not recipient:
            return {"valid": False, "errors": ["Missing push token"]}
        return {"valid": True, "errors": []}

    def health_check(self):
        return {"status": "OK", "mode": "demo", "provider": self.provider_code}

    def send(self, recipient, subject, body, metadata=None):
        validation = self.validate(recipient)
        if not validation["valid"]:
            return {"success": False, "error": validation["errors"][0]}
        return {
            "success": True,
            "mode": "demo",
            "provider_message_id": f"PUSH-{uuid.uuid4().hex[:10].upper()}",
            "channel": self.channel,
            "to": recipient,
            "title": subject,
        }


class WebhookProvider(BaseNotificationProvider):
    channel = "WEBHOOK"
    provider_code = "WEBHOOK_DEMO"

    def validate(self, recipient: str):
        if not recipient or not recipient.startswith("http"):
            return {"valid": False, "errors": ["Invalid webhook URL"]}
        return {"valid": True, "errors": []}

    def health_check(self):
        return {"status": "OK", "mode": "demo", "provider": self.provider_code}

    def send(self, recipient, subject, body, metadata=None):
        validation = self.validate(recipient)
        if not validation["valid"]:
            return {"success": False, "error": validation["errors"][0]}
        return {
            "success": True,
            "mode": "demo",
            "provider_message_id": f"WH-{uuid.uuid4().hex[:10].upper()}",
            "channel": self.channel,
            "target_url": recipient,
        }


class InAppProvider(BaseNotificationProvider):
    channel = "IN_APP"
    provider_code = "IN_APP"

    def validate(self, recipient: str):
        if not recipient:
            return {"valid": False, "errors": ["Missing user id"]}
        return {"valid": True, "errors": []}

    def health_check(self):
        return {"status": "OK", "mode": "internal", "provider": self.provider_code}

    def send(self, recipient, subject, body, metadata=None):
        validation = self.validate(recipient)
        if not validation["valid"]:
            return {"success": False, "error": validation["errors"][0]}
        return {
            "success": True,
            "mode": "internal",
            "provider_message_id": f"INAPP-{uuid.uuid4().hex[:10].upper()}",
            "channel": self.channel,
            "user_id": recipient,
        }
