import json
import re
from datetime import datetime

from app.models.notification_center import NCNotificationPreference


class NotificationRouter:
    @staticmethod
    def render_template(template_body, variables=None):
        variables = variables or {}
        rendered = template_body
        for key, value in variables.items():
            rendered = rendered.replace(f"{{{{{key}}}}}", str(value))
        remaining = re.findall(r"\{\{([^}]+)\}\}", rendered)
        return rendered, remaining

    @staticmethod
    def resolve_channels(user_id, channel, priority="NORMAL"):
        pref = NCNotificationPreference.query.filter_by(user_id=user_id).first()
        if pref is None:
            return [channel]

        if priority == "CRITICAL" and pref.critical_override:
            return [channel]

        now_hour = datetime.utcnow().hour
        if pref.mute_start_hour is not None and pref.mute_end_hour is not None:
            start = pref.mute_start_hour
            end = pref.mute_end_hour
            muted = start <= now_hour < end if start <= end else now_hour >= start or now_hour < end
            if muted and priority != "CRITICAL":
                return ["IN_APP"]

        channel_map = {
            "EMAIL": pref.email_enabled,
            "SMS": pref.sms_enabled,
            "PUSH": pref.push_enabled,
            "ZALO": pref.zalo_enabled,
            "WEBHOOK": pref.webhook_enabled,
            "IN_APP": True,
        }
        if channel_map.get(channel, True):
            return [channel]
        return ["IN_APP"]
