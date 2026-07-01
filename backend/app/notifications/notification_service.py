import json
import uuid

from app.core.statuses import (
    DOMAIN_EVENT_BOOKING_CREATED,
    DOMAIN_EVENT_COLLECTOR_ASSIGNED,
    DOMAIN_EVENT_CRITICAL_RESULT,
    DOMAIN_EVENT_INVOICE_CREATED,
    DOMAIN_EVENT_INVOICE_PAID,
    DOMAIN_EVENT_PARTNER_APPROVED,
    DOMAIN_EVENT_RESULT_APPROVED,
    DOMAIN_EVENT_SAMPLE_COLLECTED,
    DOMAIN_EVENT_SAMPLE_RECEIVED,
    NC_NOTIFICATION_QUEUED,
)
from app.extensions.db import db
from app.models.notification_center import (
    NCNotification,
    NCNotificationPreference,
    NCNotificationProvider,
    NCNotificationTemplate,
)
from app.notifications.notification_manager import NotificationManager
from app.notifications.notification_registry import NotificationRegistry
from app.notifications.notification_router import NotificationRouter


class NotificationCenterError(Exception):
    def __init__(self, message, status_code=400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class NotificationCenterService:
    @staticmethod
    def ensure_defaults():
        NotificationRegistry.initialize()
        if NCNotificationProvider.query.first():
            return {"seeded": False}

        providers = [
            ("EMAIL_SMTP", "Email SMTP Provider", "EMAIL"),
            ("SMS_DEMO", "SMS Demo Provider", "SMS"),
            ("ZALO_DEMO", "Zalo OA Demo Provider", "ZALO"),
            ("PUSH_DEMO", "Push Demo Provider", "PUSH"),
            ("WEBHOOK_DEMO", "Webhook Demo Provider", "WEBHOOK"),
            ("IN_APP", "In-App Provider", "IN_APP"),
        ]
        for code, name, channel in providers:
            db.session.add(
                NCNotificationProvider(
                    provider_code=code,
                    name=name,
                    channel=channel,
                    health_status="OK",
                )
            )
        db.session.add(
            NCNotificationPreference(
                user_id="demo-user",
                email_enabled=True,
                sms_enabled=True,
                push_enabled=True,
                zalo_enabled=True,
                webhook_enabled=True,
                mute_start_hour=22,
                mute_end_hour=6,
                critical_override=True,
            )
        )
        db.session.commit()
        return {"seeded": True}

    @staticmethod
    def list_notifications(status=None, limit=100):
        query = NCNotification.query
        if status:
            query = query.filter_by(status=status)
        rows = query.order_by(NCNotification.created_at.desc()).limit(min(limit, 500)).all()
        return {"count": len(rows), "notifications": [row.to_dict() for row in rows]}

    @staticmethod
    def get_notification(notification_id):
        from app.models.notification_center import NCNotificationDelivery

        row = NCNotification.query.filter_by(id=notification_id).first()
        if row is None:
            raise NotificationCenterError("Notification not found", 404)
        deliveries = NCNotificationDelivery.query.filter_by(notification_id=row.id).all()
        payload = row.to_dict()
        payload["deliveries"] = [item.to_dict() for item in deliveries]
        return payload

    @staticmethod
    def create_notification(data, dispatch=True):
        channel = (data.get("channel") or "EMAIL").upper()
        recipient = data.get("recipient")
        if not recipient:
            raise NotificationCenterError("recipient is required")

        user_id = data.get("user_id") or recipient
        channels = NotificationRouter.resolve_channels(user_id, channel, data.get("priority") or "NORMAL")
        channel = channels[0]

        template = None
        template_id = data.get("template_id")
        if template_id:
            template = NCNotificationTemplate.query.filter_by(id=template_id).first()
        elif data.get("template_code"):
            template = NCNotificationTemplate.query.filter_by(template_code=data["template_code"]).first()

        body = data.get("body") or (template.body if template else "DxCon notification")
        subject = data.get("subject") or (template.subject if template else "DxCon")
        variables = data.get("variables") or {}
        if template:
            body, _ = NotificationRouter.render_template(body, variables)
            if subject:
                subject, _ = NotificationRouter.render_template(subject, variables)

        provider = NCNotificationProvider.query.filter_by(channel=channel, status="ACTIVE").first()
        notification = NCNotification(
            notification_code=data.get("notification_code") or f"NC-{uuid.uuid4().hex[:8].upper()}",
            event_type=data.get("event_type"),
            channel=channel,
            recipient=recipient,
            subject=subject,
            body=body,
            status=NC_NOTIFICATION_QUEUED,
            priority=data.get("priority") or "NORMAL",
            template_id=template.id if template else None,
            provider_id=provider.id if provider else None,
            metadata_json=json.dumps(data.get("metadata") or {}),
        )
        db.session.add(notification)
        db.session.commit()
        should_dispatch = data.get("dispatch", dispatch)
        if should_dispatch is not False:
            return NotificationManager.dispatch(notification, variables)
        return {"notification": notification.to_dict()}

    @staticmethod
    def retry_notification(notification_id):
        try:
            return NotificationManager.retry_notification(notification_id)
        except ValueError as exc:
            raise NotificationCenterError(str(exc), 404 if "not found" in str(exc) else 400)

    @staticmethod
    def list_providers():
        NotificationRegistry.initialize()
        rows = NCNotificationProvider.query.order_by(NCNotificationProvider.channel.asc()).all()
        registry = {item["channel"]: item for item in NotificationRegistry.list_providers()}
        items = []
        for row in rows:
            payload = row.to_dict()
            payload["runtime_health"] = registry.get(row.channel, {}).get("health", {})
            items.append(payload)
        return {"count": len(items), "providers": items}

    @staticmethod
    def statistics():
        rows = NCNotification.query.all()
        total = len(rows)
        by_status = {}
        latencies = []
        for row in rows:
            by_status[row.status] = by_status.get(row.status, 0) + 1
            if row.latency_ms:
                latencies.append(row.latency_ms)
        sent = by_status.get("SENT", 0)
        failed = by_status.get("FAILED", 0)
        success_rate = round((sent / total) * 100, 2) if total else 0
        avg_latency = round(sum(latencies) / len(latencies), 2) if latencies else 0
        return {
            "total": total,
            "queued": by_status.get("QUEUED", 0),
            "processing": by_status.get("PROCESSING", 0),
            "sent": sent,
            "failed": failed,
            "retry": by_status.get("RETRY", 0),
            "cancelled": by_status.get("CANCELLED", 0),
            "average_latency_ms": avg_latency,
            "delivery_success_rate": success_rate,
        }


class NotificationTemplateService:
    @staticmethod
    def list_templates(channel=None):
        query = NCNotificationTemplate.query
        if channel:
            query = query.filter_by(channel=channel.upper())
        rows = query.order_by(NCNotificationTemplate.template_code.asc()).all()
        return {"count": len(rows), "templates": [row.to_dict() for row in rows]}

    @staticmethod
    def create_template(data):
        if not data.get("name") or not data.get("body"):
            raise NotificationCenterError("name and body are required")
        row = NCNotificationTemplate(
            template_code=data.get("template_code") or f"TPL-{uuid.uuid4().hex[:8].upper()}",
            name=data["name"],
            channel=(data.get("channel") or "EMAIL").upper(),
            language=data.get("language") or "vi",
            subject=data.get("subject"),
            body=data["body"],
            variables_json=json.dumps(data.get("variables") or []),
        )
        db.session.add(row)
        db.session.commit()
        return row.to_dict()

    @staticmethod
    def update_template(template_id, data):
        row = NCNotificationTemplate.query.filter_by(id=template_id).first()
        if row is None:
            raise NotificationCenterError("Template not found", 404)
        for field in ("name", "channel", "language", "subject", "body", "status"):
            if field in data and data[field] is not None:
                setattr(row, field, data[field])
        if "variables" in data:
            row.variables_json = json.dumps(data["variables"] or [])
        db.session.commit()
        return row.to_dict()


class NotificationEventSubscriber:
    EVENT_CHANNELS = {
        DOMAIN_EVENT_BOOKING_CREATED: "EMAIL",
        DOMAIN_EVENT_SAMPLE_COLLECTED: "SMS",
        DOMAIN_EVENT_SAMPLE_RECEIVED: "IN_APP",
        DOMAIN_EVENT_RESULT_APPROVED: "EMAIL",
        DOMAIN_EVENT_CRITICAL_RESULT: "SMS",
        DOMAIN_EVENT_INVOICE_CREATED: "EMAIL",
        DOMAIN_EVENT_INVOICE_PAID: "EMAIL",
        DOMAIN_EVENT_COLLECTOR_ASSIGNED: "PUSH",
        DOMAIN_EVENT_PARTNER_APPROVED: "WEBHOOK",
    }

    @staticmethod
    def handle_event(event):
        channel = NotificationEventSubscriber.EVENT_CHANNELS.get(event.event_type, "IN_APP")
        payload = event.payload or {}
        recipient = payload.get("recipient") or payload.get("email") or payload.get("user_id") or "demo-user@example.com"
        return NotificationCenterService.create_notification(
            {
                "event_type": event.event_type,
                "channel": channel,
                "recipient": recipient,
                "priority": "CRITICAL" if event.event_type == DOMAIN_EVENT_CRITICAL_RESULT else "NORMAL",
                "variables": payload,
                "body": payload.get("body") or f"Event {event.event_type} notification",
                "subject": payload.get("subject") or f"DxCon: {event.event_type}",
            }
        )

    @staticmethod
    def register():
        from app.events.event_bus import EventBus

        for event_type in NotificationEventSubscriber.EVENT_CHANNELS.keys():
            EventBus.subscribe(event_type, NotificationEventSubscriber.handle_event)
        return {"subscribed": list(NotificationEventSubscriber.EVENT_CHANNELS.keys())}
