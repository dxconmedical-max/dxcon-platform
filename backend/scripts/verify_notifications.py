import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.core.statuses import (
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
from app.services.communication_hub_service import (
    CommunicationHubService,
    EventHubService,
    NotificationCenterService,
    QueueHubService,
    TemplateHubService,
    WebhookHubService,
)


def verify_models_import():
    models = [
        WorkflowAutomationEvent,
        WebhookEndpoint,
        WebhookDeliveryLog,
        CommunicationQueueItem,
        CommunicationDeadLetter,
        CommunicationDeliveryTrack,
    ]
    for model in models:
        assert model.__tablename__
        print("OK: model", model.__name__)
    return True


def verify_routes(app):
    routes = {str(rule) for rule in app.url_map.iter_rules()}
    required_api = [
        "/api/v1/notifications/hub",
        "/api/v1/notifications/hub/send",
        "/api/v1/notifications/queue",
        "/api/v1/notifications/queue/process",
        "/api/v1/notifications/queue/<queue_item_id>/retry",
        "/api/v1/notifications/deliveries",
        "/api/v1/notifications/dead-letter",
        "/api/v1/templates",
        "/api/v1/templates/<template_id>",
        "/api/v1/webhooks",
        "/api/v1/webhooks/deliveries",
        "/api/v1/webhooks/<webhook_id>/test",
        "/api/v1/events",
        "/api/v1/events/types",
    ]
    required_web = [
        "/notifications",
        "/events",
        "/templates",
        "/webhooks",
    ]
    for route in required_api + required_web:
        if route in routes:
            print("OK:", route)
        else:
            print("MISSING:", route)
            return False
    return True


def verify_no_duplicate_routes(app):
    prefixes = (
        "/api/v1/notifications/",
        "/api/v1/templates",
        "/api/v1/webhooks",
        "/api/v1/events",
    )
    seen = set()
    for rule in app.url_map.iter_rules():
        path = str(rule.rule)
        if not any(path.startswith(prefix) or path == prefix.rstrip("/") for prefix in prefixes):
            if path not in {"/notifications", "/events", "/templates", "/webhooks"}:
                continue
        key = (path, tuple(sorted(rule.methods)))
        if key in seen:
            print("DUPLICATE:", key)
            return False
        seen.add(key)
    print("OK: no duplicate communication routes")
    return True


def verify_engines():
    with app.app_context():
        db.create_all()
        seed = CommunicationHubService.ensure_defaults()
        if not seed.get("seeded") and TemplateHubService.list_templates()["count"] < 1:
            print("MISSING: default templates")
            return False
        print("OK: templates seeded")

        templates = TemplateHubService.list_templates(channel="EMAIL")
        if templates["count"] < 1:
            print("MISSING: email templates")
            return False
        print("OK: email/sms/push templates")

        send = NotificationCenterService.send_multichannel(
            {
                "recipient": "patient@example.com",
                "channels": [NOTIFICATION_CHANNEL_EMAIL, NOTIFICATION_CHANNEL_SMS, NOTIFICATION_CHANNEL_PUSH],
                "subject": "Verify",
                "body": "Verification message",
            }
        )
        if send["queued"] < 1:
            print("MISSING: notification center send")
            return False
        print("OK: notification center channels")

        event_types = EventHubService.list_event_types()["event_types"]
        expected = [
            EVENT_BOOKING_CREATED,
            EVENT_COLLECTOR_ASSIGNED,
            EVENT_SAMPLE_RECEIVED,
            EVENT_LAB_COMPLETED,
            EVENT_RESULT_APPROVED,
            EVENT_CRITICAL_RESULT,
            EVENT_INVOICE_PAID,
            EVENT_CONTRACT_EXPIRED,
        ]
        for item in expected:
            if item not in event_types:
                print("MISSING: event type", item)
                return False
        print("OK: workflow events")

        emitted = EventHubService.emit(
            {"event_type": EVENT_LAB_COMPLETED, "recipient": "lab@example.com", "payload": {"order_id": "O1"}}
        )
        if emitted["event"]["status"] != "PROCESSED":
            print("MISSING: workflow automation")
            return False
        print("OK: workflow automation")

        webhooks = WebhookHubService.list_webhooks()
        if webhooks["count"] < 1:
            print("MISSING: webhooks")
            return False
        print("OK: webhooks")

        forced = QueueHubService.enqueue(
            {"channel": NOTIFICATION_CHANNEL_EMAIL, "recipient": "", "max_retries": 1}
        )
        QueueHubService.process_queue(limit=5, force_fail=True)
        QueueHubService.process_queue(limit=5, force_fail=True)
        if CommunicationDeadLetter.query.count() < 1:
            print("MISSING: dead-letter queue")
            return False
        print("OK: dead-letter queue")

        if CommunicationDeliveryTrack.query.count() < 1:
            print("MISSING: delivery tracking")
            return False
        print("OK: delivery tracking")

        retry = QueueHubService.retry(forced["id"])
        if retry["status"] != "PENDING":
            print("MISSING: queue retry")
            return False
        print("OK: queue retry")
        return True


app = create_app()
print("\n=== DXCON COMMUNICATION HUB VERIFY ===\n")
errors = 0
if not verify_models_import():
    errors += 1
if not verify_routes(app):
    errors += 1
if not verify_no_duplicate_routes(app):
    errors += 1
if not verify_engines():
    errors += 1
if errors:
    print("\nFAILED:", errors, "issue(s)")
    sys.exit(1)
print("\nCOMMUNICATION HUB VERIFY PASSED\n")
