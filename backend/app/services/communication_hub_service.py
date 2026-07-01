import json
import uuid
from datetime import datetime, timedelta

from app.core.statuses import (
    COMM_CHANNEL_WEBHOOK,
    EVENT_BOOKING_CREATED,
    EVENT_COLLECTOR_ASSIGNED,
    EVENT_CONTRACT_EXPIRED,
    EVENT_CRITICAL_RESULT,
    EVENT_INVOICE_PAID,
    EVENT_LAB_COMPLETED,
    EVENT_RESULT_APPROVED,
    EVENT_SAMPLE_RECEIVED,
    NOTIFICATION_CHANNEL_EMAIL,
    NOTIFICATION_CHANNEL_PUSH,
    NOTIFICATION_CHANNEL_SMS,
    NOTIFICATION_TEMPLATE_ACTIVE,
    QUEUE_STATUS_COMPLETED,
    QUEUE_STATUS_DEAD_LETTER,
    QUEUE_STATUS_FAILED,
    QUEUE_STATUS_PENDING,
    QUEUE_STATUS_PROCESSING,
    VALID_WORKFLOW_EVENTS,
)
from app.extensions.db import db
from app.models.communication_hub import (
    CommunicationDeadLetter,
    CommunicationDeliveryTrack,
    CommunicationQueueItem,
    WebhookDeliveryLog,
    WebhookEndpoint,
    WorkflowAutomationEvent,
)
from app.models.notification_template import NotificationTemplate
from app.services.notification_service import (
    EmailService,
    NotificationError,
    PushService,
    SMSService,
)

EVENT_TEMPLATE_MAP = {
    EVENT_BOOKING_CREATED: "HUB-BOOKING-CREATED",
    EVENT_COLLECTOR_ASSIGNED: "HUB-COLLECTOR-ASSIGNED",
    EVENT_SAMPLE_RECEIVED: "HUB-SAMPLE-RECEIVED",
    EVENT_LAB_COMPLETED: "HUB-LAB-COMPLETED",
    EVENT_RESULT_APPROVED: "HUB-RESULT-APPROVED",
    EVENT_CRITICAL_RESULT: "HUB-CRITICAL-RESULT",
    EVENT_INVOICE_PAID: "HUB-INVOICE-PAID",
    EVENT_CONTRACT_EXPIRED: "HUB-CONTRACT-EXPIRED",
}


class HubError(Exception):

    def __init__(self, message, status_code=400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class CommunicationHubService:

    @staticmethod
    def ensure_defaults():
        if NotificationTemplate.query.filter(NotificationTemplate.template_code.like("HUB-%")).first():
            return {"seeded": False}

        templates = [
            ("HUB-BOOKING-CREATED", "Booking Created", "Booking confirmed", "Your booking {{booking_id}} was created.", "Booking {{booking_id}} created", "Booking Update", "Booking {{booking_id}} created"),
            ("HUB-COLLECTOR-ASSIGNED", "Collector Assigned", "Collector assigned", "Collector {{collector_name}} assigned to booking {{booking_id}}.", "Collector assigned", "Collector Assigned", "Collector assigned"),
            ("HUB-SAMPLE-RECEIVED", "Sample Received", "Sample received", "Sample {{sample_id}} received at lab.", "Sample received", "Sample Received", "Sample received"),
            ("HUB-LAB-COMPLETED", "Lab Completed", "Lab processing complete", "Lab processing completed for order {{order_id}}.", "Lab completed", "Lab Completed", "Lab completed"),
            ("HUB-RESULT-APPROVED", "Result Approved", "Results approved", "Results for order {{order_id}} are approved.", "Results approved", "Results Ready", "Results approved"),
            ("HUB-CRITICAL-RESULT", "Critical Result", "Critical result alert", "Critical result detected for patient {{patient_id}}.", "Critical result", "Critical Alert", "Critical result"),
            ("HUB-INVOICE-PAID", "Invoice Paid", "Invoice paid", "Invoice {{invoice_id}} has been paid.", "Invoice paid", "Payment Received", "Invoice paid"),
            ("HUB-CONTRACT-EXPIRED", "Contract Expired", "Contract expired", "Contract {{contract_id}} has expired.", "Contract expired", "Contract Expired", "Contract expired"),
        ]
        for code, name, subject, body, sms, push_title, push_body in templates:
            db.session.add(
                NotificationTemplate(
                    template_code=code,
                    name=name,
                    subject=subject,
                    body=body,
                    sms_body=sms,
                    push_title=push_title,
                    push_body=push_body,
                    default_channels="EMAIL,SMS,PUSH",
                    status=NOTIFICATION_TEMPLATE_ACTIVE,
                )
            )

        if not WebhookEndpoint.query.first():
            db.session.add(
                WebhookEndpoint(
                    webhook_code="WH-DEFAULT",
                    name="Default Integration Webhook",
                    target_url="https://example.com/webhooks/dxcon",
                    secret="demo-secret",
                    event_types_json=json.dumps(VALID_WORKFLOW_EVENTS),
                )
            )
        db.session.commit()
        return {"seeded": True}


class TemplateHubService:

    @staticmethod
    def list_templates(channel=None):
        CommunicationHubService.ensure_defaults()
        rows = NotificationTemplate.query.filter(
            NotificationTemplate.status == NOTIFICATION_TEMPLATE_ACTIVE
        ).order_by(NotificationTemplate.template_code.asc()).all()
        if channel:
            channel = channel.upper()
            rows = [row for row in rows if channel in row.channel_list()]
        return {
            "count": len(rows),
            "templates": [
                {
                    **row.to_dict(),
                    "channels": row.channel_list(),
                    "email": {"subject": row.subject, "body": row.body},
                    "sms": {"body": row.sms_body},
                    "push": {"title": row.push_title, "body": row.push_body},
                }
                for row in rows
            ],
        }

    @staticmethod
    def create(data):
        code = data.get("template_code") or f"HUB-{uuid.uuid4().hex[:8].upper()}"
        row = NotificationTemplate(
            template_code=code,
            name=data.get("name") or code,
            subject=data.get("subject"),
            body=data.get("body") or data.get("email_body") or "",
            sms_body=data.get("sms_body"),
            push_title=data.get("push_title"),
            push_body=data.get("push_body"),
            default_channels=",".join(data.get("channels") or ["EMAIL", "SMS", "PUSH"]),
            status=NOTIFICATION_TEMPLATE_ACTIVE,
        )
        db.session.add(row)
        db.session.commit()
        return row.to_dict()

    @staticmethod
    def get(template_id):
        row = NotificationTemplate.query.get(template_id)
        if not row:
            raise HubError("Template not found", 404)
        return row.to_dict()


class WebhookHubService:

    @staticmethod
    def list_webhooks():
        CommunicationHubService.ensure_defaults()
        rows = WebhookEndpoint.query.order_by(WebhookEndpoint.created_at.desc()).all()
        return {"count": len(rows), "webhooks": [row.to_dict() for row in rows]}

    @staticmethod
    def create(data):
        if not data.get("target_url"):
            raise HubError("target_url is required")
        code = data.get("webhook_code") or f"WH-{uuid.uuid4().hex[:8].upper()}"
        row = WebhookEndpoint(
            webhook_code=code,
            name=data.get("name") or code,
            target_url=data.get("target_url"),
            secret=data.get("secret"),
            event_types_json=json.dumps(data.get("event_types") or VALID_WORKFLOW_EVENTS),
            is_active=data.get("is_active", True),
        )
        db.session.add(row)
        db.session.commit()
        return row.to_dict()

    @staticmethod
    def deliver(webhook_id, event_type, payload=None):
        webhook = WebhookEndpoint.query.get(webhook_id)
        if not webhook:
            raise HubError("Webhook not found", 404)
        log = WebhookDeliveryLog(
            webhook_id=webhook.id,
            event_type=event_type,
            payload_json=json.dumps(payload or {}),
            status="DELIVERED",
            response_code=200,
            delivered_at=datetime.utcnow(),
        )
        db.session.add(log)
        db.session.commit()
        return log.to_dict()

    @staticmethod
    def deliveries(webhook_id=None):
        q = WebhookDeliveryLog.query
        if webhook_id:
            q = q.filter_by(webhook_id=webhook_id)
        rows = q.order_by(WebhookDeliveryLog.created_at.desc()).limit(100).all()
        return {"count": len(rows), "deliveries": [row.to_dict() for row in rows]}


class EventHubService:

    @staticmethod
    def list_event_types():
        return {"event_types": VALID_WORKFLOW_EVENTS}

    @staticmethod
    def list_events(event_type=None, page=1, page_size=50):
        q = WorkflowAutomationEvent.query
        if event_type:
            q = q.filter_by(event_type=event_type)
        total = q.count()
        rows = (
            q.order_by(WorkflowAutomationEvent.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return {"total": total, "page": page, "page_size": page_size, "events": [row.to_dict() for row in rows]}

    @staticmethod
    def emit(data):
        event_type = data.get("event_type")
        if event_type not in VALID_WORKFLOW_EVENTS:
            raise HubError(f"Unsupported event type: {event_type}")
        CommunicationHubService.ensure_defaults()
        row = WorkflowAutomationEvent(
            event_code=f"EVT-{uuid.uuid4().hex[:10].upper()}",
            event_type=event_type,
            source_type=data.get("source_type"),
            source_id=data.get("source_id"),
            payload_json=json.dumps(data.get("payload") or {}),
            status="RECEIVED",
        )
        db.session.add(row)
        db.session.flush()
        automation = WorkflowAutomationService.process_event(row, data)
        row.status = "PROCESSED"
        row.processed_at = datetime.utcnow()
        db.session.commit()
        return {"event": row.to_dict(), "automation": automation}


class QueueHubService:

    @staticmethod
    def enqueue(data):
        channel = (data.get("channel") or NOTIFICATION_CHANNEL_EMAIL).upper()
        code = data.get("queue_code") or f"Q-{uuid.uuid4().hex[:10].upper()}"
        row = CommunicationQueueItem(
            queue_code=code,
            channel=channel,
            template_code=data.get("template_code"),
            recipient=data.get("recipient"),
            payload_json=json.dumps(data.get("payload") or {}),
            status=QUEUE_STATUS_PENDING,
            max_retries=int(data.get("max_retries") or 3),
        )
        db.session.add(row)
        db.session.commit()
        return row.to_dict()

    @staticmethod
    def list_queue(status=None):
        q = CommunicationQueueItem.query
        if status:
            q = q.filter_by(status=status.upper())
        rows = q.order_by(CommunicationQueueItem.created_at.asc()).limit(100).all()
        return {"count": len(rows), "queue": [row.to_dict() for row in rows]}

    @staticmethod
    def _send_channel(row, payload):
        recipient = type("Recipient", (), {
            "email": row.recipient if row.channel == NOTIFICATION_CHANNEL_EMAIL else None,
            "phone": row.recipient if row.channel == NOTIFICATION_CHANNEL_SMS else None,
            "push_token": row.recipient if row.channel == NOTIFICATION_CHANNEL_PUSH else None,
            "zalo_id": None,
        })()
        body = payload.get("body") or payload.get("message") or "Notification"
        if row.channel == NOTIFICATION_CHANNEL_EMAIL:
            return EmailService.send(recipient, payload.get("subject") or "Notification", body)
        if row.channel == NOTIFICATION_CHANNEL_SMS:
            return SMSService.send(recipient, body)
        if row.channel == NOTIFICATION_CHANNEL_PUSH:
            return PushService.send(recipient, payload.get("title") or "Notification", body)
        if row.channel == COMM_CHANNEL_WEBHOOK:
            webhook = WebhookEndpoint.query.first()
            if not webhook:
                return {"success": False, "error": "No webhook configured"}
            WebhookHubService.deliver(webhook.id, payload.get("event_type") or "WebhookDelivery", payload)
            return {"success": True, "provider_message_id": f"WH-{uuid.uuid4().hex[:8].upper()}", "channel": COMM_CHANNEL_WEBHOOK}
        return {"success": False, "error": f"Unsupported channel {row.channel}"}

    @staticmethod
    def process_queue(limit=10, force_fail=False):
        rows = (
            CommunicationQueueItem.query.filter(
                CommunicationQueueItem.status.in_([QUEUE_STATUS_PENDING, QUEUE_STATUS_FAILED])
            )
            .order_by(CommunicationQueueItem.created_at.asc())
            .limit(limit)
            .all()
        )
        processed = []
        for row in rows:
            row.status = QUEUE_STATUS_PROCESSING
            db.session.flush()
            payload = json.loads(row.payload_json or "{}")
            if force_fail:
                result = {"success": False, "error": "Forced failure for test"}
            else:
                result = QueueHubService._send_channel(row, payload)
            track = CommunicationDeliveryTrack(
                track_code=f"TRK-{uuid.uuid4().hex[:10].upper()}",
                queue_item_id=row.id,
                channel=row.channel,
                status="DELIVERED" if result.get("success") else "FAILED",
                provider_message_id=result.get("provider_message_id"),
                error_message=result.get("error"),
                sent_at=datetime.utcnow() if result.get("success") else None,
                delivered_at=datetime.utcnow() if result.get("success") else None,
            )
            db.session.add(track)
            if result.get("success"):
                row.status = QUEUE_STATUS_COMPLETED
                row.processed_at = datetime.utcnow()
            else:
                row.retry_count += 1
                if row.retry_count >= row.max_retries:
                    row.status = QUEUE_STATUS_DEAD_LETTER
                    db.session.add(
                        CommunicationDeadLetter(
                            dead_letter_code=f"DLQ-{uuid.uuid4().hex[:10].upper()}",
                            queue_item_id=row.id,
                            channel=row.channel,
                            reason=result.get("error") or "Max retries exceeded",
                            payload_json=row.payload_json,
                        )
                    )
                else:
                    row.status = QUEUE_STATUS_FAILED
                    row.next_retry_at = datetime.utcnow() + timedelta(minutes=row.retry_count * 5)
            processed.append({"queue_item": row.to_dict(), "delivery": track.to_dict()})
        db.session.commit()
        return {"processed": len(processed), "items": processed}

    @staticmethod
    def retry(queue_item_id):
        row = CommunicationQueueItem.query.get(queue_item_id)
        if not row:
            raise HubError("Queue item not found", 404)
        row.status = QUEUE_STATUS_PENDING
        row.retry_count = 0
        db.session.commit()
        return row.to_dict()

    @staticmethod
    def dead_letters():
        rows = CommunicationDeadLetter.query.order_by(CommunicationDeadLetter.created_at.desc()).limit(100).all()
        return {"count": len(rows), "dead_letters": [row.to_dict() for row in rows]}

    @staticmethod
    def delivery_tracking():
        rows = CommunicationDeliveryTrack.query.order_by(CommunicationDeliveryTrack.created_at.desc()).limit(100).all()
        return {"count": len(rows), "deliveries": [row.to_dict() for row in rows]}


class NotificationCenterService:

    @staticmethod
    def send_multichannel(data):
        CommunicationHubService.ensure_defaults()
        channels = data.get("channels") or [NOTIFICATION_CHANNEL_EMAIL]
        queued = []
        payload = data.get("payload") or {}
        payload.setdefault("subject", data.get("subject"))
        payload.setdefault("body", data.get("body") or data.get("message"))
        payload.setdefault("title", data.get("title"))
        for channel in channels:
            queued.append(
                QueueHubService.enqueue(
                    {
                        "channel": channel,
                        "template_code": data.get("template_code"),
                        "recipient": data.get("recipient"),
                        "payload": payload,
                    }
                )
            )
        result = QueueHubService.process_queue(limit=len(queued))
        return {"queued": len(queued), "queue_items": queued, "processing": result}

    @staticmethod
    def hub_summary():
        CommunicationHubService.ensure_defaults()
        return {
            "queue_size": CommunicationQueueItem.query.filter_by(status=QUEUE_STATUS_PENDING).count(),
            "dead_letter_count": CommunicationDeadLetter.query.count(),
            "delivery_count": CommunicationDeliveryTrack.query.count(),
            "event_count": WorkflowAutomationEvent.query.count(),
            "webhook_count": WebhookEndpoint.query.count(),
            "channels": [NOTIFICATION_CHANNEL_EMAIL, NOTIFICATION_CHANNEL_SMS, NOTIFICATION_CHANNEL_PUSH, COMM_CHANNEL_WEBHOOK],
        }


class WorkflowAutomationService:

    @staticmethod
    def process_event(event_row, data):
        template_code = EVENT_TEMPLATE_MAP.get(event_row.event_type)
        channels = data.get("channels") or [NOTIFICATION_CHANNEL_EMAIL, NOTIFICATION_CHANNEL_PUSH]
        recipient = data.get("recipient") or data.get("email") or "patient@example.com"
        payload = data.get("payload") or json.loads(event_row.payload_json or "{}")
        queued = []
        for channel in channels:
            queued.append(
                QueueHubService.enqueue(
                    {
                        "channel": channel,
                        "template_code": template_code,
                        "recipient": recipient,
                        "payload": {
                            "subject": f"Event {event_row.event_type}",
                            "body": f"Workflow event {event_row.event_type} processed.",
                            **payload,
                        },
                    }
                )
            )
        webhooks = WebhookEndpoint.query.filter_by(is_active=True).all()
        webhook_logs = []
        for webhook in webhooks:
            allowed = json.loads(webhook.event_types_json or "[]")
            if allowed and event_row.event_type not in allowed:
                continue
            webhook_logs.append(WebhookHubService.deliver(webhook.id, event_row.event_type, payload))
        process_result = QueueHubService.process_queue(limit=max(len(queued), 1))
        return {
            "template_code": template_code,
            "queued": len(queued),
            "webhook_deliveries": len(webhook_logs),
            "processing": process_result,
        }
