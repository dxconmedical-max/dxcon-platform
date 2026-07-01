import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.extensions.db import db
from scripts.seed_observability_demo import seed_observability_demo


class MetricsPlatformTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()
        seed_observability_demo()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def test_metrics_endpoints(self):
        for path in ("/api/v1/metrics", "/api/v1/metrics/system", "/api/v1/metrics/business"):
            response = self.client.get(path)
            self.assertEqual(response.status_code, 200, path)
            self.assertIsInstance(response.get_json(), dict)

    def test_prometheus_endpoint(self):
        response = self.client.get("/metrics/prometheus")
        self.assertEqual(response.status_code, 200)
        self.assertIn("http_requests_total", response.data.decode())


if __name__ == "__main__":
    unittest.main()
