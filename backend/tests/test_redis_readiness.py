import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.infrastructure.production_readiness import check_redis_health, validate_redis


class RedisReadinessTestCase(unittest.TestCase):
    def test_dev_degrades_without_redis(self):
        app = create_app()
        app.config.update({"APP_ENV": "development", "REDIS_URL": "", "TESTING": True})
        payload = check_redis_health(app)
        self.assertEqual(payload["status"], "DEGRADED")
        self.assertTrue(payload["ok"])
        validate_redis(app)

    def test_production_requires_redis(self):
        app = create_app()
        app.config.update({"APP_ENV": "production", "REDIS_URL": "", "TESTING": False})
        payload = check_redis_health(app)
        self.assertEqual(payload["status"], "DOWN")
        self.assertFalse(payload["ok"])
        with self.assertRaises(RuntimeError):
            validate_redis(app)


if __name__ == "__main__":
    unittest.main()
