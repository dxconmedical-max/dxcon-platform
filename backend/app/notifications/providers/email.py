import smtplib
import uuid
from email.mime.text import MIMEText

from flask import current_app

from app.notifications.providers.base import BaseNotificationProvider


class EmailProvider(BaseNotificationProvider):
    channel = "EMAIL"
    provider_code = "EMAIL_SMTP"

    def validate(self, recipient: str):
        if not recipient or "@" not in recipient:
            return {"valid": False, "errors": ["Invalid email recipient"]}
        return {"valid": True, "errors": []}

    def health_check(self):
        app = current_app._get_current_object()
        host = app.config.get("SMTP_HOST")
        if not host:
            return {"status": "DEGRADED", "detail": "SMTP not configured; demo mode active"}
        return {"status": "OK", "host": host, "port": app.config.get("SMTP_PORT")}

    def send(self, recipient, subject, body, metadata=None):
        validation = self.validate(recipient)
        if not validation["valid"]:
            return {"success": False, "error": validation["errors"][0]}

        app = current_app._get_current_object()
        host = app.config.get("SMTP_HOST")
        if not host:
            return {
                "success": True,
                "mode": "demo",
                "provider_message_id": f"EMAIL-DEMO-{uuid.uuid4().hex[:10].upper()}",
                "channel": self.channel,
            }

        msg = MIMEText(body, "plain", "utf-8")
        msg["Subject"] = subject or "DxCon Notification"
        msg["From"] = app.config.get("SMTP_FROM") or app.config.get("SMTP_USER")
        msg["To"] = recipient
        try:
            with smtplib.SMTP(host, app.config.get("SMTP_PORT", 587), timeout=10) as server:
                if app.config.get("SMTP_USE_TLS", True):
                    server.starttls()
                user = app.config.get("SMTP_USER")
                password = app.config.get("SMTP_PASSWORD")
                if user and password:
                    server.login(user, password)
                server.send_message(msg)
            return {
                "success": True,
                "mode": "smtp",
                "provider_message_id": f"EMAIL-{uuid.uuid4().hex[:10].upper()}",
                "channel": self.channel,
            }
        except Exception as exc:
            return {"success": False, "error": str(exc), "channel": self.channel}
