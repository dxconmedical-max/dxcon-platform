import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.core.api_response import api_envelope
from app.core.errors import build_error_response
from app.core.list_params import parse_filters, parse_pagination_args, parse_sort
from app.core.startup_checks import run_startup_checks
from app.extensions.db import db


class GoLiveDay1TestCase(unittest.TestCase):
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

    def test_api_envelope_shape(self):
        with self.app.test_request_context("/api/v1/system/health"):
            payload = api_envelope(True, data={"ok": True}, error=None)
            self.assertTrue(payload["success"])
            self.assertEqual(payload["data"], {"ok": True})
            self.assertIsNone(payload["error"])
            self.assertIn("request_id", payload)
            self.assertIn("timestamp", payload)

    def test_error_envelope_shape(self):
        with self.app.test_request_context("/api/v1/system/health"):
            payload, status = build_error_response("NOT_FOUND", "missing", 404)
            self.assertEqual(status, 404)
            self.assertFalse(payload["success"])
            self.assertIsNone(payload["data"])
            self.assertEqual(payload["error"]["code"], "NOT_FOUND")
            self.assertIn("request_id", payload)
            self.assertIn("timestamp", payload)

    def test_liveness_readiness_aliases(self):
        for path in ("/api/v1/system/liveness", "/api/v1/system/readiness"):
            response = self.client.get(path)
            self.assertIn(response.status_code, {200, 503}, path)

    def test_trace_headers(self):
        response = self.client.get(
            "/api/v1/system/health",
            headers={
                "X-Request-ID": "req-go-live",
                "X-Correlation-ID": "corr-go-live",
                "X-Trace-ID": "trace-go-live",
                "X-Tenant-ID": "tenant-go-live",
            },
        )
        self.assertEqual(response.headers.get("X-Request-ID"), "req-go-live")
        self.assertEqual(response.headers.get("X-Correlation-ID"), "corr-go-live")
        self.assertEqual(response.headers.get("X-Trace-ID"), "trace-go-live")

    def test_startup_checks(self):
        result = run_startup_checks(self.app)
        self.assertIn(result["status"], {"OK", "DEGRADED"})
        names = {item["name"] for item in result["checks"]}
        self.assertTrue({"storage", "jwt", "scheduler", "plugins"}.issubset(names))

    def test_list_params(self):
        page, per_page = parse_pagination_args({"page": "2", "page_size": "25"})
        self.assertEqual(page, 2)
        self.assertEqual(per_page, 25)
        sort_field, direction = parse_sort({"sort": "created_at", "direction": "desc"}, {"created_at", "name"})
        self.assertEqual(sort_field, "created_at")
        self.assertEqual(direction, "desc")
        filters = parse_filters({"status": "ACTIVE", "ignored": "x"}, {"status"})
        self.assertEqual(filters, {"status": "ACTIVE"})

    def test_config_summary(self):
        from app.core.config_validation import config_summary

        summary = config_summary(self.app)
        self.assertIn("database_configured", summary)
        self.assertIn("redis_configured", summary)
        self.assertIn("smtp_configured", summary)


if __name__ == "__main__":
    unittest.main()
