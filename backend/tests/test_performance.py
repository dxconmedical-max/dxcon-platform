import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.core.background_tasks import background_tasks
from app.core.cache import cache, cache_delete, cache_get, cache_set
from app.core.db_pool import build_engine_options, review_pool_config
from app.core.pagination import paginate_query, pagination_payload
from app.core.performance_metrics import performance_metrics
from app.extensions.db import db
from app.models.company import Company


class PerformanceTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()
        cache.clear()
        performance_metrics.query_count = 0
        performance_metrics.query_time_ms_total = 0.0
        performance_metrics.slow_query_count = 0
        performance_metrics.cache_hits = 0
        performance_metrics.cache_misses = 0

        for index in range(15):
            db.session.add(
                Company(
                    company_code=f"C-{index:03d}",
                    company_name=f"Company {index}",
                    tax_code=f"T-{index}",
                )
            )
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def test_engine_options_for_sqlite(self):
        options = build_engine_options("sqlite:///:memory:")
        self.assertIn("connect_args", options)

    def test_engine_options_for_postgres(self):
        options = build_engine_options("postgresql://user:pass@localhost/db")
        self.assertTrue(options.get("pool_pre_ping"))
        self.assertEqual(options.get("pool_size"), 5)

    def test_pool_review(self):
        review = review_pool_config(self.app)
        self.assertIn("ok", review)
        self.assertIn("engine_options", review)

    def test_pagination_helper(self):
        query = Company.query.order_by(Company.company_code)
        result = paginate_query(query, page=2, per_page=5)
        self.assertEqual(len(result["items"]), 5)
        self.assertEqual(result["pagination"]["page"], 2)
        self.assertEqual(result["pagination"]["total"], 15)
        self.assertTrue(result["pagination"]["has_prev"])
        self.assertTrue(result["pagination"]["has_next"])

        payload = pagination_payload(
            result["items"],
            result["pagination"],
            serializer=lambda item: item.company_code,
        )
        self.assertEqual(len(payload["items"]), 5)

    def test_cache_abstraction(self):
        cache_set("company-count", 15, ttl_seconds=30)
        self.assertEqual(cache_get("company-count"), 15)
        self.assertGreaterEqual(performance_metrics.cache_hits, 1)

        cache_delete("company-count")
        self.assertIsNone(cache_get("company-count"))
        self.assertGreaterEqual(performance_metrics.cache_misses, 1)

    def test_background_task_runner(self):
        state = {"value": 0}

        def increment():
            state["value"] += 1

        task_id, result = background_tasks.run_sync(increment)
        self.assertTrue(task_id)
        self.assertIsNone(result)
        self.assertEqual(state["value"], 1)
        self.assertEqual(background_tasks.snapshot()["completed"], 1)

    def test_performance_metrics_endpoint(self):
        self.client.get("/api/v1/system/health")
        response = self.client.get("/api/v1/system/performance")
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertIn("query_count", payload)
        self.assertIn("cache_hit_rate", payload)
        self.assertIn("background_tasks", payload)
        self.assertIn("database_pool", payload)

    def test_sqlalchemy_query_metrics_recorded(self):
        self.client.get("/api/v1/system/stats")
        self.assertGreaterEqual(performance_metrics.query_count, 1)


if __name__ == "__main__":
    unittest.main()
