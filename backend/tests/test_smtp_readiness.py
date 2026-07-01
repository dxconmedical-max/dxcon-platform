import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.infrastructure.production_readiness import check_smtp_readiness, validate_smtp


class SmtpReadinessTestCase(unittest.TestCase):
    def test_dev_optional_smtp(self):
        app = create_app()
        app.config.update({"APP_ENV": "development", "TESTING": True})
        payload = check_smtp_readiness(app)
        self.assertEqual(payload["status"], "DEGRADED")
        self.assertTrue(payload["ok"])
        validate_smtp(app)

    def test_production_requires_smtp(self):
        app = create_app()
        app.config.update({"APP_ENV": "production", "TESTING": False})
        payload = check_smtp_readiness(app)
        self.assertTrue(payload["blocker"])
        self.assertFalse(payload["ok"])
        with self.assertRaises(RuntimeError):
            validate_smtp(app)

    def test_production_accepts_complete_smtp(self):
        app = create_app()
        app.config.update(
            {
                "APP_ENV": "production",
                "TESTING": False,
                "SMTP_HOST": "smtp.test",
                "SMTP_PORT": 587,
                "SMTP_FROM": "noreply@test",
            }
        )
        payload = check_smtp_readiness(app)
        self.assertEqual(payload["status"], "OK")
        self.assertTrue(payload["ok"])


if __name__ == "__main__":
    unittest.main()
