import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.infrastructure.production_readiness import database_dialect_report, validate_database


class DatabaseReadinessTestCase(unittest.TestCase):
    def test_dev_allows_sqlite(self):
        app = create_app()
        app.config.update({"APP_ENV": "development", "TESTING": True})
        report = database_dialect_report(app)
        self.assertTrue(report["ok"])
        validate_database(app)

    def test_staging_blocks_sqlite(self):
        app = create_app()
        app.config.update(
            {
                "APP_ENV": "staging",
                "TESTING": False,
                "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
                "CORS_ORIGINS": "https://staging.dxcon.test",
            }
        )
        report = database_dialect_report(app)
        self.assertFalse(report["ok"])
        with self.assertRaises(RuntimeError):
            validate_database(app)

    def test_staging_accepts_postgresql(self):
        app = create_app()
        app.config.update(
            {
                "APP_ENV": "staging",
                "TESTING": False,
                "SQLALCHEMY_DATABASE_URI": "postgresql://dxcon:dxcon@localhost/dxcon",
                "CORS_ORIGINS": "https://staging.dxcon.test",
                "REDIS_URL": "redis://localhost:6379/0",
                "SMTP_HOST": "smtp.test",
                "SMTP_PORT": 587,
                "SMTP_FROM": "noreply@test",
            }
        )
        report = database_dialect_report(app)
        self.assertEqual(report["dialect"], "postgresql")
        self.assertTrue(report["ok"])


if __name__ == "__main__":
    unittest.main()
