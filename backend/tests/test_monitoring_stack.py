import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

from scripts.monitoring_stack_lib import (
    REQUIRED_ALERTS,
    REQUIRED_DASHBOARD_PANELS,
    REQUIRED_PROMETHEUS_METRICS,
    run_monitoring_stack_verification,
    run_uat_monitoring_smoke,
    verify_alert_rules,
    verify_grafana_provisioning,
    verify_prometheus_config,
)


class MonitoringStackTestCase(unittest.TestCase):
    def test_prometheus_config(self):
        result = verify_prometheus_config()
        self.assertTrue(result["ok"], result)

    def test_alert_rules(self):
        result = verify_alert_rules()
        self.assertTrue(result["ok"], result)
        self.assertEqual(len(result["present"]), len(REQUIRED_ALERTS))

    def test_grafana_provisioning(self):
        result = verify_grafana_provisioning()
        self.assertTrue(result["ok"], result)
        for panel in REQUIRED_DASHBOARD_PANELS:
            self.assertNotIn(panel, result.get("missing_panels", []))

    def test_full_monitoring_verification(self):
        result = run_monitoring_stack_verification()
        self.assertTrue(result["ok"], result)

    def test_uat_monitoring_smoke(self):
        result = run_uat_monitoring_smoke()
        self.assertTrue(result["ok"], result)


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

    def test_prometheus_endpoint_exports_required_metrics(self):
        self.client.get("/live")
        response = self.client.get("/metrics/prometheus")
        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        for metric in REQUIRED_PROMETHEUS_METRICS:
            self.assertIn(metric, body, f"missing metric {metric}")

    def test_system_metrics_endpoint(self):
        response = self.client.get("/api/v1/system/metrics")
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertIn("requests", payload)


if __name__ == "__main__":
    unittest.main()
