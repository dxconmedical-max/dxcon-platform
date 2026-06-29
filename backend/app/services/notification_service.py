import json
import uuid
from datetime import datetime

from app.core.audit import write_audit
from app.core.statuses import (
    NOTIFICATION_CHANNEL_EMAIL,
    NOTIFICATION_CHANNEL_IN_APP,
    NOTIFICATION_CHANNEL_PUSH,
    NOTIFICATION_CHANNEL_SMS,
    NOTIFICATION_CHANNEL_ZALO,
    NOTIFICATION_DELIVERY_DELIVERED,
    NOTIFICATION_DELIVERY_FAILED,
    NOTIFICATION_DELIVERY_SENT,
    NOTIFICATION_STATUS_DELIVERED,
    NOTIFICATION_STATUS_FAILED,
    NOTIFICATION_STATUS_QUEUED,
    NOTIFICATION_STATUS_SENT,
    NOTIFICATION_TEMPLATE_ACTIVE,
    VALID_NOTIFICATION_CHANNELS,
)
from app.extensions.db import db
from app.models.notification import Notification
from app.models.notification_delivery import NotificationDelivery
from app.models.notification_preference import NotificationPreference
from app.models.notification_recipient import NotificationRecipient
from app.models.notification_template import NotificationTemplate


class NotificationError(Exception):

    def __init__(self, message, status_code=400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class NotificationQueue:

    _queue = []

    @classmethod
    def enqueue(cls, notification_id):
        if notification_id not in cls._queue:
            cls._queue.append(notification_id)
        return notification_id

    @classmethod
    def dequeue(cls):
        if not cls._queue:
            return None
        return cls._queue.pop(0)

    @classmethod
    def size(cls):
        return len(cls._queue)

    @classmethod
    def clear(cls):
        cls._queue = []


class EmailService:

    @staticmethod
    def send(recipient, subject, body):
        if not recipient.email:
            return {"success": False, "error": "Missing email address"}
        message_id = f"EMAIL-{uuid.uuid4().hex[:12].upper()}"
        return {
            "success": True,
            "provider_message_id": message_id,
            "channel": NOTIFICATION_CHANNEL_EMAIL,
            "to": recipient.email,
            "subject": subject,
        }


class SMSService:

    @staticmethod
    def send(recipient, body):
        if not recipient.phone:
            return {"success": False, "error": "Missing phone number"}
        message_id = f"SMS-{uuid.uuid4().hex[:12].upper()}"
        return {
            "success": True,
            "provider_message_id": message_id,
            "channel": NOTIFICATION_CHANNEL_SMS,
            "to": recipient.phone,
        }


class ZaloService:

    @staticmethod
    def send(recipient, body):
        if not recipient.zalo_id and not recipient.phone:
            return {"success": False, "error": "Missing Zalo recipient"}
        message_id = f"ZALO-{uuid.uuid4().hex[:12].upper()}"
        return {
            "success": True,
            "provider_message_id": message_id,
            "channel": NOTIFICATION_CHANNEL_ZALO,
            "to": recipient.zalo_id or recipient.phone,
        }


class PushService:

    @staticmethod
    def send(recipient, title, body):
        if not recipient.push_token:
            return {"success": False, "error": "Missing push token"}
        message_id = f"PUSH-{uuid.uuid4().hex[:12].upper()}"
        return {
            "success": True,
            "provider_message_id": message_id,
            "channel": NOTIFICATION_CHANNEL_PUSH,
            "to": recipient.push_token,
            "title": title,
        }


class NotificationService:

    CHANNEL_SENDERS = {
        NOTIFICATION_CHANNEL_EMAIL: EmailService,
        NOTIFICATION_CHANNEL_SMS: SMSService,
        NOTIFICATION_CHANNEL_ZALO: ZaloService,
        NOTIFICATION_CHANNEL_PUSH: PushService,
    }

    @staticmethod
    def _generate_code():
        count = Notification.query.count()
        return f"NTF-{count + 1:06d}"

    @staticmethod
    def list_templates():
        return (
            NotificationTemplate.query.filter_by(status=NOTIFICATION_TEMPLATE_ACTIVE)
            .order_by(NotificationTemplate.template_code.asc())
            .all()
        )

    @staticmethod
    def get_template(template_code):
        template = NotificationTemplate.query.filter_by(
            template_code=template_code,
            status=NOTIFICATION_TEMPLATE_ACTIVE,
        ).first()
        if not template:
            raise NotificationError(f"Template {template_code} not found", 404)
        return template

    @staticmethod
    def _render(template_text, context):
        rendered = template_text or ""
        for key, value in (context or {}).items():
            rendered = rendered.replace(f"{{{key}}}", str(value or ""))
        return rendered

    @staticmethod
    def _resolve_channels(template, requested_channels=None):
        if requested_channels:
            return [channel for channel in requested_channels if channel in VALID_NOTIFICATION_CHANNELS]
        return template.channel_list() or [NOTIFICATION_CHANNEL_IN_APP]

    @staticmethod
    def _is_channel_enabled(user_id, channel, template_code):
        if not user_id:
            return True
        pref = NotificationPreference.query.filter_by(
            user_id=user_id,
            channel=channel,
            template_code=template_code,
        ).first()
        if pref:
            return pref.is_enabled
        global_pref = NotificationPreference.query.filter_by(
            user_id=user_id,
            channel=channel,
            template_code=None,
        ).first()
        if global_pref:
            return global_pref.is_enabled
        return True

    @staticmethod
    def _create_recipients(notification, recipients):
        created = []
        for item in recipients or []:
            row = NotificationRecipient(
                notification_id=notification.id,
                recipient_type=item.get("recipient_type", "USER"),
                recipient_id=item.get("recipient_id"),
                recipient_name=item.get("recipient_name"),
                email=item.get("email"),
                phone=item.get("phone"),
                zalo_id=item.get("zalo_id"),
                push_token=item.get("push_token"),
            )
            db.session.add(row)
            created.append(row)
        db.session.flush()
        return created

    @staticmethod
    def _dispatch_channel(notification, template, recipient, channel):
        delivery = NotificationDelivery(
            notification_id=notification.id,
            recipient_id=recipient.id,
            channel=channel,
        )
        db.session.add(delivery)
        db.session.flush()

        if channel == NOTIFICATION_CHANNEL_IN_APP:
            delivery.status = NOTIFICATION_DELIVERY_DELIVERED
            delivery.delivered_at = datetime.utcnow()
            return delivery

        if not NotificationService._is_channel_enabled(
            recipient.recipient_id,
            channel,
            notification.template_code,
        ):
            delivery.status = NOTIFICATION_DELIVERY_FAILED
            delivery.error_message = "Channel disabled by preference"
            return delivery

        sender = NotificationService.CHANNEL_SENDERS.get(channel)
        if not sender:
            delivery.status = NOTIFICATION_DELIVERY_FAILED
            delivery.error_message = f"Unsupported channel {channel}"
            return delivery

        if channel == NOTIFICATION_CHANNEL_EMAIL:
            result = sender.send(recipient, notification.subject, notification.body)
        elif channel == NOTIFICATION_CHANNEL_SMS:
            sms_body = NotificationService._render(template.sms_body or notification.body, {})
            result = sender.send(recipient, sms_body)
        elif channel == NOTIFICATION_CHANNEL_ZALO:
            zalo_body = NotificationService._render(template.zalo_body or notification.body, {})
            result = sender.send(recipient, zalo_body)
        elif channel == NOTIFICATION_CHANNEL_PUSH:
            push_title = template.push_title or notification.subject
            push_body = NotificationService._render(template.push_body or notification.body, {})
            result = sender.send(recipient, push_title, push_body)
        else:
            result = {"success": False, "error": "Unknown channel"}

        delivery.sent_at = datetime.utcnow()
        if result.get("success"):
            delivery.status = NOTIFICATION_DELIVERY_SENT
            delivery.provider_message_id = result.get("provider_message_id")
            delivery.delivered_at = datetime.utcnow()
            delivery.status = NOTIFICATION_DELIVERY_DELIVERED
        else:
            delivery.status = NOTIFICATION_DELIVERY_FAILED
            delivery.error_message = result.get("error")
        return delivery

    @staticmethod
    def process_notification(notification_id):
        notification = Notification.query.get(notification_id)
        if not notification:
            raise NotificationError("Notification not found", 404)

        template = NotificationService.get_template(notification.template_code)
        recipients = NotificationRecipient.query.filter_by(notification_id=notification.id).all()
        metadata = json.loads(notification.metadata_json or "{}")
        channels = NotificationService._resolve_channels(template, metadata.get("channels"))

        deliveries = []
        for recipient in recipients:
            for channel in channels:
                deliveries.append(
                    NotificationService._dispatch_channel(
                        notification,
                        template,
                        recipient,
                        channel,
                    )
                )

        failed = [row for row in deliveries if row.status == NOTIFICATION_DELIVERY_FAILED]
        notification.sent_at = datetime.utcnow()
        if failed and len(failed) == len(deliveries):
            notification.status = NOTIFICATION_STATUS_FAILED
        elif failed:
            notification.status = NOTIFICATION_STATUS_SENT
        else:
            notification.status = NOTIFICATION_STATUS_DELIVERED
        db.session.commit()
        return notification, deliveries

    @staticmethod
    def create_notification(data, actor_email="SYSTEM", ip_address="", process_immediately=True):
        template_code = data.get("template_code")
        if not template_code:
            raise NotificationError("template_code is required", 400)

        template = NotificationService.get_template(template_code)
        context = data.get("context") or {}
        subject = NotificationService._render(
            data.get("subject") or template.subject or template.name,
            context,
        )
        body = NotificationService._render(data.get("body") or template.body, context)

        recipients = data.get("recipients") or []
        if not recipients:
            raise NotificationError("At least one recipient is required", 400)

        metadata = {
            "channels": data.get("channels") or template.channel_list(),
            "context": context,
        }

        notification = Notification(
            notification_code=NotificationService._generate_code(),
            template_code=template.template_code,
            subject=subject,
            body=body,
            status=NOTIFICATION_STATUS_QUEUED,
            priority=data.get("priority", "NORMAL"),
            reference_type=data.get("reference_type"),
            reference_id=data.get("reference_id"),
            metadata_json=json.dumps(metadata),
        )
        db.session.add(notification)
        db.session.flush()

        NotificationService._create_recipients(notification, recipients)
        NotificationQueue.enqueue(notification.id)
        write_audit("NOTIFICATION_CREATE", "Notification", notification.id, actor_email, ip_address)
        db.session.commit()

        if process_immediately:
            notification, deliveries = NotificationService.process_notification(notification.id)
            return notification, deliveries
        return notification, []

    @staticmethod
    def send(data, actor_email="SYSTEM", ip_address=""):
        notification, deliveries = NotificationService.create_notification(
            data,
            actor_email=actor_email,
            ip_address=ip_address,
            process_immediately=True,
        )
        return notification, deliveries

    @staticmethod
    def send_bulk(items, actor_email="SYSTEM", ip_address=""):
        results = []
        for item in items or []:
            notification, deliveries = NotificationService.send(
                item,
                actor_email=actor_email,
                ip_address=ip_address,
            )
            results.append(
                {
                    "notification": notification.to_dict(include_deliveries=True),
                    "delivery_count": len(deliveries),
                }
            )
        return results

    @staticmethod
    def send_test(data, actor_email="SYSTEM", ip_address=""):
        payload = dict(data or {})
        payload.setdefault("template_code", "WELCOME")
        payload.setdefault(
            "recipients",
            [
                {
                    "recipient_name": "Test User",
                    "email": payload.get("email", "test@dxcon.vn"),
                    "phone": payload.get("phone", "0900000000"),
                    "push_token": payload.get("push_token", "firebase-test-token"),
                    "zalo_id": payload.get("zalo_id", "zalo-test-id"),
                }
            ],
        )
        payload["context"] = payload.get("context") or {"name": "Test User"}
        notification, deliveries = NotificationService.send(
            payload,
            actor_email=actor_email,
            ip_address=ip_address,
        )
        return notification, deliveries

    @staticmethod
    def list_notifications(status=None, template_code=None):
        query = Notification.query
        if status:
            query = query.filter(Notification.status == status)
        if template_code:
            query = query.filter(Notification.template_code == template_code)
        return query.order_by(Notification.created_at.desc()).all()

    @staticmethod
    def get_notification(notification_id):
        notification = Notification.query.get(notification_id)
        if not notification:
            raise NotificationError("Notification not found", 404)
        return notification.to_dict(include_recipients=True, include_deliveries=True)
