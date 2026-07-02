import json
import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

from app.core.logging_config import JsonLogFormatter, redact_mapping, sanitize_path
from app.observability.logging_service import StructuredLoggingService
from scripts.monitoring_stack_lib import REQUIRED_PROMETHEUS_METRICS, verify_log_readiness


class LogSafetyTestCase(unittest.TestCase):
    def setUp(self):
        from app import create_app

        self.app = create_app()
        self.app.config.update({"TESTING": True, "LOG_FORMAT": "json"})
        self.client = self.app.test_client()

    def test_json_formatter_output(self):
        import logging

        formatter = JsonLogFormatter()
        record = logging.LogRecord(
            name="dxcon.test",
            level=logging.INFO,
            pathname=__file__,
            lineno=1,
            msg="safe message",
            args=(),
            exc_info=None,
        )
        record.request_id = "req-log-1"
        record.correlation_id = "corr-log-1"
        payload = json.loads(formatter.format(record))
        self.assertEqual(payload["level"], "INFO")
        self.assertEqual(payload["request_id"], "req-log-1")

    def test_sensitive_fields_redacted(self):
        redacted = redact_mapping({"password": "secret", "email": "a@b.com"})
        self.assertEqual(redacted["password"], "[REDACTED]")
        self.assertEqual(redacted["email"], "a@b.com")

    def test_query_string_redaction(self):
        sanitized = sanitize_path("/api/v1/auth/login?token=abc&page=1")
        self.assertIn("token=[REDACTED]", sanitized)
        self.assertIn("page=1", sanitized)

    def test_structured_logging_redaction(self):
        cleaned = StructuredLoggingService.sanitize({"api_key": "abc", "status": "OK"})
        self.assertEqual(cleaned["api_key"], "[REDACTED]")

    def test_request_and_correlation_headers(self):
        result = verify_log_readiness()
        self.assertTrue(result["checks"]["request_id_header"], result)
        self.assertTrue(result["checks"]["json_log_format"], result)
        self.assertTrue(result["checks"]["password_redacted"], result)


class PrometheusMetricsExportTestCase(unittest.TestCase):
    def setUp(self):
        from app import create_app
        from app.extensions.db import db

        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()

    def tearDown(self):
        from app.extensions.db import db

        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def test_http_request_records_metrics(self):
        from app.observability.metrics_service import MetricsPlatformService

        MetricsPlatformService.record_http_request(12.5, 500)
        MetricsPlatformService.refresh_runtime_metrics(self.app)
        body = self.client.get("/metrics/prometheus").get_data(as_text=True)
        self.assertIn("http_requests_total", body)
        self.assertIn("http_errors_total", body)
        for metric in REQUIRED_PROMETHEUS_METRICS:
            self.assertIn(metric, body)


if __name__ == "__main__":
    unittest.main()
