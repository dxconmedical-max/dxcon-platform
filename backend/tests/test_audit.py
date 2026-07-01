import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.extensions.db import db
from app.models.observability_platform import AuditEvent
from app.observability.audit_service import AuditTimelineService


class AuditPlatformTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def test_audit_timeline(self):
        event = AuditTimelineService.record(
            event_type="Login",
            action="login_success",
            actor={"actor_code": "ACT-1", "display_name": "Demo User", "user_id": "u1"},
            resource={"resource_code": "RES-1", "resource_id": "session-1", "resource_type": "Login"},
        )
        self.assertEqual(AuditEvent.query.count(), 1)
        self.assertEqual(event["event_type"], "Login")

        listed = AuditTimelineService.list_events()
        self.assertGreaterEqual(listed["count"], 1)


if __name__ == "__main__":
    unittest.main()
