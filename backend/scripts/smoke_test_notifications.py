import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.core.statuses import (
    EVENT_BOOKING_CREATED,
    NOTIFICATION_CHANNEL_EMAIL,
    NOTIFICATION_CHANNEL_PUSH,
    NOTIFICATION_CHANNEL_SMS,
)
from app.extensions.db import db
from app.services.communication_hub_service import CommunicationHubService


def smoke_test():
    with app.app_context():
        db.create_all()
        CommunicationHubService.ensure_defaults()
        steps = [
            ("GET hub summary", "get", "/api/v1/notifications/hub", None),
            (
                "POST hub send",
                "post",
                "/api/v1/notifications/hub/send",
                {
                    "recipient": "patient@example.com",
                    "channels": [NOTIFICATION_CHANNEL_EMAIL, NOTIFICATION_CHANNEL_SMS, NOTIFICATION_CHANNEL_PUSH],
                    "subject": "Smoke Test",
                    "body": "Communication hub smoke test",
                },
            ),
            ("GET queue", "get", "/api/v1/notifications/queue", None),
            ("GET deliveries", "get", "/api/v1/notifications/deliveries", None),
            ("GET templates", "get", "/api/v1/templates", None),
            ("GET webhooks", "get", "/api/v1/hub/webhooks", None),
            ("GET event types", "get", "/api/v1/hub/events/types", None),
            (
                "POST event",
                "post",
                "/api/v1/hub/events",
                {"event_type": EVENT_BOOKING_CREATED, "recipient": "ops@example.com", "payload": {"booking_id": "B-100"}},
            ),
            ("GET notifications dashboard", "get", "/notifications", None),
            ("GET events dashboard", "get", "/events", None),
            ("GET templates dashboard", "get", "/templates", None),
            ("GET webhooks dashboard", "get", "/webhooks", None),
        ]
        for label, method, path, payload in steps:
            if method == "get":
                response = client.get(path)
            else:
                response = client.post(path, json=payload or {})
            if response.status_code >= 400:
                print("FAIL:", label, response.status_code, response.get_data(as_text=True)[:200])
                return False
            print("OK:", label, response.status_code)
        return True


app = create_app()
app.config["TESTING"] = True
client = app.test_client()
print("\n=== DXCON COMMUNICATION HUB SMOKE TEST ===\n")
if not smoke_test():
    print("\nCOMMUNICATION HUB SMOKE TEST FAILED\n")
    sys.exit(1)
print("\nCOMMUNICATION HUB SMOKE TEST PASSED\n")
