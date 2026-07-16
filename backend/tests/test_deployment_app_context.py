"""Regression tests for deployment startup application-context handling."""

from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from flask import has_app_context
from sqlalchemy.exc import OperationalError

from app import create_app
from app.core.database_startup import verify_database_connection
from app.core.deployment import init_deployment
from app.extensions.db import db


class DeploymentAppContextTestCase(unittest.TestCase):
    def test_create_app_boots_with_startup_db_validation(self):
        """create_app() succeeds with STARTUP_VALIDATE_DB enabled (no app-context crash)."""
        app = create_app()
        app.config["TESTING"] = True
        deployment = app.extensions.get("dxcon_deployment", {})
        self.assertTrue(deployment.get("startup_complete"))
        migration = deployment.get("migration_status") or {}
        error = str(migration.get("error") or "")
        self.assertNotIn("Working outside of application context", error)

    def test_init_deployment_runs_db_checks_inside_app_context(self):
        app = create_app()
        app.config.update(
            {
                "TESTING": False,
                "STARTUP_VALIDATE_DB": True,
                "APP_ENV": "development",
                "DB_CONNECT_RETRIES": 1,
                "DB_CONNECT_RETRY_DELAY_SECONDS": 0,
            }
        )

        seen = {"in_context": False}

        def fake_startup_database_check(check_app):
            seen["in_context"] = has_app_context()
            return {
                "ready": True,
                "alembic_present": False,
                "table_count": 0,
                "missing_core_tables": [],
            }

        with patch("app.core.deployment.validate_config"):
            with patch(
                "app.core.database_startup.startup_database_check",
                side_effect=fake_startup_database_check,
            ):
                status = init_deployment(app)

        self.assertTrue(seen["in_context"])
        self.assertTrue(status.get("ready"))

    def test_init_deployment_testing_mode_skips_db_checks(self):
        app = create_app()
        app.config["TESTING"] = True
        with patch("app.core.deployment.validate_startup") as mocked:
            result = init_deployment(app)
            mocked.assert_not_called()
        self.assertTrue(result.get("testing"))
        self.assertTrue(app.extensions["dxcon_deployment"]["startup_complete"])

    def test_db_connectivity_failure_preserves_database_error(self):
        app = create_app()
        app.config["TESTING"] = True
        with app.app_context():
            operational = OperationalError(
                "SELECT 1", {}, Exception("connection refused")
            )
            with patch.object(db.session, "execute", side_effect=operational):
                with self.assertRaises(RuntimeError) as ctx:
                    verify_database_connection(app, retries=1, delay_seconds=0)

        message = str(ctx.exception)
        self.assertIn("connection refused", message.lower())
        self.assertNotIn("Working outside of application context", message)

    def test_db_failure_outside_context_does_not_mask_with_rollback(self):
        """Without an app context, rollback must not replace the original error."""
        app = create_app()
        app.config["TESTING"] = True
        with self.assertRaises(RuntimeError) as ctx:
            verify_database_connection(app, retries=1, delay_seconds=0)
        message = str(ctx.exception)
        self.assertIn("Database connection failed", message)
        # Original failure may mention context; rollback must not add a second mask.
        self.assertEqual(message.count("Working outside of application context"), 1)

    def test_staging_init_deployment_uses_app_context(self):
        app = create_app()
        app.config.update(
            {
                "TESTING": False,
                "APP_ENV": "staging",
                "STARTUP_VALIDATE_DB": True,
                "DB_CONNECT_RETRIES": 1,
                "DB_CONNECT_RETRY_DELAY_SECONDS": 0,
            }
        )

        context_during_check = {"value": False}

        def fake_startup_database_check(check_app):
            context_during_check["value"] = has_app_context()
            return {
                "ready": True,
                "alembic_present": False,
                "table_count": 3,
                "missing_core_tables": [],
            }

        with patch("app.core.deployment.validate_config"):
            with patch(
                "app.core.database_startup.startup_database_check",
                side_effect=fake_startup_database_check,
            ):
                status = init_deployment(app)

        self.assertTrue(context_during_check["value"])
        self.assertTrue(status.get("ready"))


if __name__ == "__main__":
    unittest.main()
