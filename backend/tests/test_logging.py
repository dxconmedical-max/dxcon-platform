import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.extensions.db import db
from app.observability.logging_service import StructuredLoggingService


class LoggingPlatformTestCase(unittest.TestCase):
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

    def test_structured_log_record(self):
        with self.app.test_request_context(
            "/api/v1/metrics",
            headers={"X-Request-ID": "req-1", "X-Trace-ID": "trace-1", "X-Correlation-ID": "corr-1"},
        ):
            from flask import g

            g.request_id = "req-1"
            g.trace_id = "trace-1"
            g.correlation_id = "corr-1"
            record = StructuredLoggingService.log_event(
                "observability",
                "test event",
                execution_ms=12.5,
                extra={"token": "secret", "module": "metrics"},
            )
            self.assertEqual(record["request_id"], "req-1")
            self.assertEqual(record["trace_id"], "trace-1")
            self.assertEqual(record["context"]["token"], "[REDACTED]")


if __name__ == "__main__":
    unittest.main()
