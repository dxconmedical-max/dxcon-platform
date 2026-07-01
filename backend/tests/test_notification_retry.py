import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.core.statuses import NC_NOTIFICATION_FAILED, NC_NOTIFICATION_RETRY, NC_NOTIFICATION_SENT
from app.extensions.db import db
from app.models.notification_center import NCNotification, NCNotificationRetry
from app.notifications.notification_manager import NotificationManager
from app.notifications.notification_service import NotificationCenterService


class NotificationRetryTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()
        NotificationCenterService.ensure_defaults()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def test_retry_flow(self):
        notification = NCNotification(
            notification_code="NC-RETRY-001",
            channel="EMAIL",
            recipient="retry@example.com",
            subject="Retry test",
            body="Body",
            status=NC_NOTIFICATION_FAILED,
        )
        db.session.add(notification)
        db.session.commit()

        with patch("app.notifications.notification_manager.NotificationRegistry.get") as mock_get:
            provider = mock_get.return_value
            provider.send.side_effect = [
                {"success": False, "error": "temporary failure"},
                {"success": True, "provider_message_id": "MSG-1"},
            ]
            provider.channel = "EMAIL"
            NotificationManager.dispatch(notification)
            self.assertEqual(notification.status, NC_NOTIFICATION_RETRY)
            retry_rows = NCNotificationRetry.query.filter_by(notification_id=notification.id).all()
            self.assertEqual(len(retry_rows), 1)
            self.assertEqual(retry_rows[0].status, NC_NOTIFICATION_RETRY)

            retry_rows[0].next_retry_at = retry_rows[0].next_retry_at.replace(year=2000)
            db.session.commit()
            NotificationManager.process_due_retries()
            db.session.refresh(notification)
            self.assertEqual(notification.status, NC_NOTIFICATION_SENT)

        api_retry = self.client.post(f"/api/v1/notifications/{notification.id}/retry")
        self.assertEqual(api_retry.status_code, 200)


if __name__ == "__main__":
    unittest.main()
