import json
import time
import uuid
from datetime import datetime, timedelta

from app.core.statuses import (
    NC_NOTIFICATION_CANCELLED,
    NC_NOTIFICATION_FAILED,
    NC_NOTIFICATION_PROCESSING,
    NC_NOTIFICATION_QUEUED,
    NC_NOTIFICATION_RETRY,
    NC_NOTIFICATION_SENT,
)
from app.extensions.db import db
from app.models.notification_center import (
    NCNotification,
    NCNotificationDelivery,
    NCNotificationProvider,
    NCNotificationRetry,
    NCNotificationTemplate,
)
from app.notifications.notification_registry import NotificationRegistry
from app.notifications.notification_router import NotificationRouter


class NotificationManager:
    MAX_RETRIES = 5

    @staticmethod
    def _provider_row(channel):
        return NCNotificationProvider.query.filter_by(channel=channel, status="ACTIVE").first()

    @staticmethod
    def dispatch(notification: NCNotification, variables=None):
        NotificationRegistry.initialize()
        provider_row = NotificationManager._provider_row(notification.channel)
        provider = NotificationRegistry.get(notification.channel)
        notification.status = NC_NOTIFICATION_PROCESSING
        db.session.commit()

        template = None
        if notification.template_id:
            template = NCNotificationTemplate.query.filter_by(id=notification.template_id).first()
        subject = notification.subject or (template.subject if template else "DxCon Notification")
        body = notification.body
        if template:
            body, _missing = NotificationRouter.render_template(template.body, variables or {})

        started = time.time()
        result = provider.send(notification.recipient, subject, body, metadata={"event_type": notification.event_type})
        latency_ms = round((time.time() - started) * 1000, 2)

        delivery = NCNotificationDelivery(
            notification_id=notification.id,
            provider_id=provider_row.id if provider_row else None,
            status=NC_NOTIFICATION_SENT if result.get("success") else NC_NOTIFICATION_FAILED,
            provider_message_id=result.get("provider_message_id"),
            error_message=result.get("error"),
            latency_ms=latency_ms,
            delivered_at=datetime.utcnow() if result.get("success") else None,
        )
        db.session.add(delivery)

        notification.latency_ms = latency_ms
        if result.get("success"):
            notification.status = NC_NOTIFICATION_SENT
            notification.sent_at = datetime.utcnow()
        else:
            notification.status = NC_NOTIFICATION_FAILED
            NotificationManager.schedule_retry(notification, result.get("error") or "Delivery failed")
        db.session.commit()
        return {"notification": notification.to_dict(), "delivery": delivery.to_dict(), "result": result}

    @staticmethod
    def schedule_retry(notification: NCNotification, error_message):
        existing = NCNotificationRetry.query.filter_by(notification_id=notification.id).count()
        attempt = existing + 1
        if attempt >= NotificationManager.MAX_RETRIES:
            notification.status = NC_NOTIFICATION_FAILED
            retry = NCNotificationRetry(
                notification_id=notification.id,
                attempt_number=attempt,
                status=NC_NOTIFICATION_FAILED,
                error_message=error_message,
            )
            db.session.add(retry)
            return retry.to_dict()

        backoff = min(60 * (2 ** (attempt - 1)), 3600)
        retry = NCNotificationRetry(
            notification_id=notification.id,
            attempt_number=attempt,
            status=NC_NOTIFICATION_RETRY,
            next_retry_at=datetime.utcnow() + timedelta(seconds=backoff),
            backoff_seconds=backoff,
            error_message=error_message,
        )
        notification.status = NC_NOTIFICATION_RETRY
        db.session.add(retry)
        return retry.to_dict()

    @staticmethod
    def retry_notification(notification_id):
        notification = NCNotification.query.filter_by(id=notification_id).first()
        if notification is None:
            raise ValueError("Notification not found")
        if notification.status == NC_NOTIFICATION_CANCELLED:
            raise ValueError("Notification is cancelled")
        return NotificationManager.dispatch(notification)

    @staticmethod
    def process_due_retries(limit=20):
        due = (
            NCNotificationRetry.query.filter(
                NCNotificationRetry.status == NC_NOTIFICATION_RETRY,
                NCNotificationRetry.next_retry_at <= datetime.utcnow(),
            )
            .order_by(NCNotificationRetry.next_retry_at.asc())
            .limit(limit)
            .all()
        )
        processed = []
        for retry_row in due:
            notification = NCNotification.query.filter_by(id=retry_row.notification_id).first()
            if notification is None:
                continue
            processed.append(NotificationManager.dispatch(notification))
        return {"count": len(processed), "items": processed}
