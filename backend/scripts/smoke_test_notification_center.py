import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.extensions.db import db
from app.notifications.notification_service import NotificationCenterService


def _payload(response):
    body = response.get_json() or {}
    if isinstance(body.get("data"), dict) and "success" in body:
        return body["data"]
    return body


def main():
    app = create_app()
    with app.app_context():
        db.create_all()
        NotificationCenterService.ensure_defaults()
        client = app.test_client()

        create = client.post(
            "/api/v1/notifications",
            json={
                "channel": "EMAIL",
                "recipient": "smoke@example.com",
                "subject": "Smoke test",
                "body": "Notification center smoke test",
            },
        )
        assert create.status_code == 201, create.data

        stats = client.get("/api/v1/notifications/statistics")
        assert stats.status_code == 200, stats.data

        providers = client.get("/api/v1/notifications/providers")
        assert providers.status_code == 200, providers.data
        assert _payload(providers)["count"] >= 6

        for page in (
            "/notifications",
            "/notifications/history",
            "/notifications/providers",
            "/notifications/templates",
            "/notifications/statistics",
        ):
            response = client.get(page)
            assert response.status_code == 200, page

    print("SMOKE TEST PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
