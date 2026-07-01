import json
import uuid
from datetime import datetime, timedelta

from app.core.statuses import NC_NOTIFICATION_QUEUED, NC_NOTIFICATION_SENT
from app.extensions.db import db
from app.models.notification_center import (
    NCNotification,
    NCNotificationProvider,
    NCNotificationTemplate,
)
from app.notifications.notification_service import NotificationCenterService


CHANNELS = ["EMAIL", "SMS", "ZALO", "PUSH", "WEBHOOK", "IN_APP"]
VARIABLES = [
    "{{patient_name}}",
    "{{order_code}}",
    "{{sample_code}}",
    "{{result_url}}",
    "{{invoice_total}}",
]


def seed_notification_center_demo():
    NotificationCenterService.ensure_defaults()

    if NCNotificationTemplate.query.count() >= 50:
        return {
            "templates": NCNotificationTemplate.query.count(),
            "notifications": NCNotification.query.count(),
            "seeded": False,
        }

    providers = {row.channel: row for row in NCNotificationProvider.query.all()}
    for index in range(50):
        channel = CHANNELS[index % len(CHANNELS)]
        db.session.add(
            NCNotificationTemplate(
                template_code=f"NC-TPL-{index + 1:03d}",
                name=f"Demo Template {index + 1}",
                channel=channel,
                language="vi" if index % 2 == 0 else "en",
                subject=f"DxCon alert for {{{{order_code}}}}",
                body=(
                    "Hello {{patient_name}}, order {{order_code}}, sample {{sample_code}}, "
                    "result {{result_url}}, total {{invoice_total}}."
                ),
                variables_json=json.dumps(VARIABLES),
            )
        )
    db.session.commit()

    templates = NCNotificationTemplate.query.all()
    statuses = [NC_NOTIFICATION_QUEUED, NC_NOTIFICATION_SENT, "FAILED", "RETRY"]
    for index in range(200):
        channel = CHANNELS[index % len(CHANNELS)]
        template = templates[index % len(templates)]
        provider = providers.get(channel)
        status = statuses[index % len(statuses)]
        notification = NCNotification(
            notification_code=f"NC-DEMO-{index + 1:04d}",
            event_type="BookingCreated" if index % 5 == 0 else "SampleCollected",
            channel=channel,
            recipient=f"user{index}@example.com" if channel == "EMAIL" else f"user-{index}",
            subject=f"Demo notification {index + 1}",
            body=template.body,
            status=status,
            priority="CRITICAL" if index % 17 == 0 else "NORMAL",
            template_id=template.id,
            provider_id=provider.id if provider else None,
            latency_ms=float(50 + (index % 120)),
            created_at=datetime.utcnow() - timedelta(hours=index % 48),
            sent_at=datetime.utcnow() - timedelta(hours=index % 24) if status == NC_NOTIFICATION_SENT else None,
        )
        db.session.add(notification)
    db.session.commit()

    return {
        "templates": NCNotificationTemplate.query.count(),
        "notifications": NCNotification.query.count(),
        "providers": NCNotificationProvider.query.count(),
        "seeded": True,
    }


if __name__ == "__main__":
    from app import create_app

    app = create_app()
    with app.app_context():
        db.create_all()
        print(seed_notification_center_demo())
