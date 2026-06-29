import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.core.statuses import NOTIFICATION_TEMPLATE_RESULT_READY
from app.extensions.db import db
from app.services.notification_service import NotificationService
from scripts.seed_notifications_demo import seed_notifications_demo


def verify_routes(app):
    routes = {str(rule) for rule in app.url_map.iter_rules()}
    required = [
        "/api/v1/notifications",
        "/api/v1/notifications/<notification_id>",
        "/api/v1/notifications/send",
        "/api/v1/notifications/bulk",
        "/api/v1/notifications/test",
        "/api/v1/notification-templates",
        "/notifications",
        "/notification-templates",
    ]
    for route in required:
        if route in routes:
            print("OK:", route)
        else:
            print("MISSING:", route)
            return False
    return True


def verify_seed_and_flow():
    with app.app_context():
        db.create_all()
        summary = seed_notifications_demo()
        if summary.get("already_seeded"):
            print("OK: notifications demo already present")
        else:
            print("OK: notifications demo seed")

        if summary.get("templates_seeded", 0) < 8 and not summary.get("already_seeded"):
            print("MISSING: notification templates")
            return False

        notification, deliveries = NotificationService.send(
            {
                "template_code": NOTIFICATION_TEMPLATE_RESULT_READY,
                "context": {"name": "Verify Patient", "order_code": "MDO-VERIFY"},
                "recipients": [
                    {
                        "recipient_name": "Verify Patient",
                        "email": "verify@dxcon.vn",
                        "phone": "0908000006",
                        "push_token": "verify-push-token",
                    }
                ],
            }
        )
        if not notification or not deliveries:
            print("MISSING: notification delivery flow")
            return False
        print("OK: notification send flow")
        return True


app = create_app()
print("\n=== DXCON NOTIFICATIONS VERIFY ===\n")
errors = 0
if not verify_routes(app):
    errors += 1
if not verify_seed_and_flow():
    errors += 1
if errors:
    print("\nFAILED:", errors, "issue(s)")
    sys.exit(1)
print("\nNOTIFICATIONS VERIFY PASSED\n")
