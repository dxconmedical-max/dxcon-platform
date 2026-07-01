import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.infrastructure.production_readiness import cors_status, validate_cors


class CorsHardeningTestCase(unittest.TestCase):
    def test_dev_allows_wildcard(self):
        app = create_app()
        app.config.update({"APP_ENV": "development", "CORS_ORIGINS": "*", "TESTING": True})
        self.assertTrue(cors_status(app)["ok"])
        validate_cors(app)

    def test_production_rejects_wildcard(self):
        app = create_app()
        app.config.update({"APP_ENV": "production", "CORS_ORIGINS": "*", "TESTING": False})
        self.assertFalse(cors_status(app)["ok"])
        with self.assertRaises(RuntimeError):
            validate_cors(app)

    def test_production_accepts_explicit_origins(self):
        app = create_app()
        app.config.update(
            {
                "APP_ENV": "production",
                "CORS_ORIGINS": "https://app.dxcon.test",
                "TESTING": False,
                "SQLALCHEMY_DATABASE_URI": "postgresql://u:p@localhost/db",
                "REDIS_URL": "redis://localhost:6379/0",
                "SMTP_HOST": "smtp.test",
                "SMTP_PORT": 587,
                "SMTP_FROM": "noreply@test",
                "STORAGE_PATH": "/tmp/dxcon",
            }
        )
        self.assertTrue(cors_status(app)["ok"])
        validate_cors(app)


if __name__ == "__main__":
    unittest.main()
