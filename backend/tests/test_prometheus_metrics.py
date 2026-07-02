import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

from app.observability.metrics_service import MetricsPlatformService
from app.observability.prometheus_exporter import prometheus_metrics_text
from scripts.monitoring_stack_lib import REQUIRED_PROMETHEUS_METRICS


class PrometheusMetricsTestCase(unittest.TestCase):
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

    def test_prometheus_text_format(self):
        MetricsPlatformService.record_http_request(25.0, 200)
        MetricsPlatformService.refresh_runtime_metrics(self.app)
        body = prometheus_metrics_text(self.app)
        self.assertIn("# HELP http_requests_total", body)
        self.assertIn("# TYPE http_requests_total counter", body)

    def test_required_runtime_metrics_present(self):
        MetricsPlatformService.refresh_runtime_metrics(self.app)
        body = prometheus_metrics_text(self.app)
        for metric in REQUIRED_PROMETHEUS_METRICS:
            self.assertIn(metric, body, f"missing {metric}")

    def test_error_counter_increments(self):
        MetricsPlatformService.record_http_request(10.0, 404)
        body = prometheus_metrics_text(self.app)
        import re

        match = re.search(r"http_errors_total (\d+(?:\.\d+)?)", body)
        self.assertIsNotNone(match)
        self.assertGreater(float(match.group(1)), 0)


if __name__ == "__main__":
    unittest.main()
