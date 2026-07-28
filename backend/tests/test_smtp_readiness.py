import os
import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.infrastructure.production_readiness import check_smtp_readiness, validate_smtp


class SmtpReadinessTestCase(unittest.TestCase):
    def test_dev_optional_smtp(self):
        app = create_app()
        app.config.update({"APP_ENV": "development", "TESTING": True, "EMAIL_DRY_RUN": False})
        payload = check_smtp_readiness(app)
        self.assertEqual(payload["status"], "DEGRADED")
        self.assertTrue(payload["ok"])
        validate_smtp(app)

    def test_production_requires_smtp(self):
        app = create_app()
        app.config.update(
            {
                "APP_ENV": "production",
                "TESTING": False,
                "EMAIL_DRY_RUN": False,
                "SMTP_HOST": "",
                "SMTP_FROM": "",
            }
        )
        payload = check_smtp_readiness(app)
        self.assertTrue(payload["blocker"])
        self.assertFalse(payload["ok"])
        with self.assertRaises(RuntimeError) as ctx:
            validate_smtp(app)
        self.assertIn("SMTP_HOST, SMTP_PORT, and SMTP_FROM are required", str(ctx.exception))

    def test_production_dry_run_allows_missing_smtp(self):
        app = create_app()
        app.config.update(
            {
                "APP_ENV": "production",
                "TESTING": False,
                "EMAIL_DRY_RUN": True,
                "SMTP_HOST": "",
                "SMTP_FROM": "",
            }
        )
        payload = check_smtp_readiness(app)
        self.assertFalse(payload["blocker"])
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["mode"], "dry_run")
        validate_smtp(app)  # must not raise

    def test_production_accepts_complete_smtp(self):
        app = create_app()
        app.config.update(
            {
                "APP_ENV": "production",
                "TESTING": False,
                "EMAIL_DRY_RUN": False,
                "SMTP_HOST": "smtp.test",
                "SMTP_PORT": 587,
                "SMTP_FROM": "noreply@test",
            }
        )
        payload = check_smtp_readiness(app)
        self.assertEqual(payload["status"], "OK")
        self.assertTrue(payload["ok"])
        validate_smtp(app)

    def test_production_incomplete_smtp_still_blocked_without_dry_run(self):
        app = create_app()
        app.config.update(
            {
                "APP_ENV": "production",
                "TESTING": False,
                "EMAIL_DRY_RUN": False,
                "SMTP_HOST": "smtp.test",
                "SMTP_PORT": 587,
                "SMTP_FROM": "",
            }
        )
        payload = check_smtp_readiness(app)
        self.assertTrue(payload["blocker"])
        self.assertIn("SMTP_FROM", payload.get("missing") or [])
        with self.assertRaises(RuntimeError):
            validate_smtp(app)


class ProductionStartupContextTestCase(unittest.TestCase):
    def test_create_app_sets_startup_complete(self):
        """gunicorn `run:app` imports create_app(); must not raise outside app context."""
        app = create_app()
        self.assertTrue(app.extensions.get("dxcon_deployment", {}).get("startup_complete"))

    def test_startup_database_check_pushes_context_when_missing(self):
        from app.core.database_startup import startup_database_check

        app = create_app()
        calls = {"n": 0}

        def fake_verify_connection(application, retries=None, delay_seconds=None):
            from flask import has_app_context

            self.assertTrue(has_app_context())
            calls["n"] += 1
            return True

        def fake_verify_migrations(application):
            from flask import has_app_context

            self.assertTrue(has_app_context())
            return {
                "ready": True,
                "table_count": 0,
                "missing_core_tables": [],
                "alembic_present": False,
            }

        with mock.patch(
            "app.core.database_startup.verify_database_connection",
            side_effect=fake_verify_connection,
        ), mock.patch(
            "app.core.database_startup.verify_migrations",
            side_effect=fake_verify_migrations,
        ):
            status = startup_database_check(app)
        self.assertTrue(status["ready"])
        self.assertEqual(calls["n"], 1)

    def test_production_create_app_succeeds_with_email_dry_run(self):
        """Render production boot: EMAIL_DRY_RUN=true + STARTUP_VALIDATE_DB can be skipped in unit test."""
        env = {
            "APP_ENV": "production",
            "DATABASE_URL": "sqlite:///:memory:",
            "REDIS_URL": "redis://localhost:6379/0",
            "CORS_ORIGINS": "https://dxcon.com.vn",
            "SECRET_KEY": "prod-secret-key-not-default-xx",
            "JWT_SECRET_KEY": "prod-jwt-secret-not-default-xx",
            "LOG_FORMAT": "json",
            "STORAGE_PATH": "/tmp/dxcon-uploads-test",
            "STARTUP_VALIDATE_DB": "false",
            "EMAIL_DRY_RUN": "true",
        }
        with mock.patch.dict(os.environ, env, clear=False):
            # Re-import Config values by constructing app with overridden config after create.
            # create_app reads Config class attrs already loaded — set via app factory patch.
            from app.core import config as config_module

            original = {
                "APP_ENV": config_module.Config.APP_ENV,
                "SQLALCHEMY_DATABASE_URI": config_module.Config.SQLALCHEMY_DATABASE_URI,
                "REDIS_URL": config_module.Config.REDIS_URL,
                "CORS_ORIGINS": config_module.Config.CORS_ORIGINS,
                "SECRET_KEY": config_module.Config.SECRET_KEY,
                "JWT_SECRET_KEY": config_module.Config.JWT_SECRET_KEY,
                "LOG_FORMAT": config_module.Config.LOG_FORMAT,
                "STORAGE_PATH": config_module.Config.STORAGE_PATH,
                "STARTUP_VALIDATE_DB": config_module.Config.STARTUP_VALIDATE_DB,
                "EMAIL_DRY_RUN": config_module.Config.EMAIL_DRY_RUN,
                "SMTP_HOST": config_module.Config.SMTP_HOST,
                "SMTP_FROM": config_module.Config.SMTP_FROM,
            }
            try:
                config_module.Config.APP_ENV = "production"
                config_module.Config.SQLALCHEMY_DATABASE_URI = "postgresql://u:p@localhost/db"
                config_module.Config.REDIS_URL = "redis://localhost:6379/0"
                config_module.Config.CORS_ORIGINS = "https://dxcon.com.vn"
                config_module.Config.SECRET_KEY = "prod-secret-key-not-default-xx"
                config_module.Config.JWT_SECRET_KEY = "prod-jwt-secret-not-default-xx"
                config_module.Config.LOG_FORMAT = "json"
                config_module.Config.STORAGE_PATH = "/tmp/dxcon-uploads-test"
                config_module.Config.STARTUP_VALIDATE_DB = False
                config_module.Config.EMAIL_DRY_RUN = True
                config_module.Config.SMTP_HOST = ""
                config_module.Config.SMTP_FROM = ""

                with mock.patch(
                    "app.infrastructure.production_readiness.check_redis_health",
                    return_value={"status": "OK", "required": True, "mode": "connected", "ok": True},
                ):
                    app = create_app()
                self.assertTrue(app.extensions.get("dxcon_deployment", {}).get("startup_complete"))
            finally:
                for key, value in original.items():
                    setattr(config_module.Config, key, value)


if __name__ == "__main__":
    unittest.main()
