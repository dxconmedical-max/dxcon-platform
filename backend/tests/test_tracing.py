import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.extensions.db import db
from app.observability.trace_service import TraceService


class TracingPlatformTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def test_trace_propagation(self):
        with self.app.test_request_context(
            "/api/v1/metrics",
            headers={"X-Trace-ID": "trace-root", "X-Span-ID": "span-parent"},
        ):
            context = TraceService.start_trace()
            self.assertEqual(context["trace_id"], "trace-root")
            child = TraceService.start_span("metrics")
            self.assertEqual(child["span"]["parent_span_id"], context["span_id"])
            headers = TraceService.inject_headers({})
            self.assertEqual(headers["X-Trace-ID"], "trace-root")

    def test_traces_dashboard(self):
        response = self.client.get("/system/traces")
        self.assertEqual(response.status_code, 200)


if __name__ == "__main__":
    unittest.main()
