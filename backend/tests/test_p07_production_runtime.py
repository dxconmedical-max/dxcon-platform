import os
import sys
import unittest
from datetime import datetime
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.core.config_validation import production_secret_is_safe, validate_config
from app.extensions.db import db
from app.infrastructure.production_readiness import (
    validate_database,
    validate_queue_provider,
    validate_redis,
)
from app.infrastructure.queue_provider import get_queue
from app.models.operations_platform import ScheduledJob, ScheduledJobRun
from app.operations.job_registry import JobRegistry
from app.operations.process_runtime import cron_matches, run_scheduler_cycle, run_worker_cycle
from scripts.apply_migrations import (
    IOT_INGEST_SECURITY,
    RECONCILIATION,
    list_migration_files,
    missing_required_migrations,
    ordered_migration_files,
)


class P07ProductionRuntimeTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def test_dev_allows_memory_queue_and_sqlite(self):
        self.app.config.update(
            {
                "APP_ENV": "development",
                "QUEUE_PROVIDER": "memory",
                "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            }
        )
        validate_queue_provider(self.app)
        validate_database(self.app)
        self.assertFalse(get_queue(self.app).durable)

    def test_production_rejects_memory_queue(self):
        self.app.config.update({"APP_ENV": "production", "QUEUE_PROVIDER": "memory"})
        with self.assertRaises(RuntimeError) as ctx:
            validate_queue_provider(self.app)
        self.assertIn("redis", str(ctx.exception).lower())

    def test_production_rejects_redis_queue_without_url(self):
        self.app.config.update(
            {
                "APP_ENV": "production",
                "QUEUE_PROVIDER": "redis",
                "REDIS_URL": "",
            }
        )
        with self.assertRaises(RuntimeError):
            validate_queue_provider(self.app)
        with self.assertRaises(RuntimeError):
            validate_redis(self.app)

    def test_production_rejects_sqlite_and_placeholder_database(self):
        self.app.config.update(
            {
                "APP_ENV": "production",
                "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            }
        )
        with self.assertRaises(RuntimeError):
            validate_database(self.app)
        self.app.config["SQLALCHEMY_DATABASE_URI"] = (
            "postgresql://dxcon:replace-me@postgres:5432/dxcon"
        )
        with self.assertRaises(RuntimeError) as ctx:
            validate_database(self.app)
        self.assertIn("placeholder", str(ctx.exception).lower())

    def test_production_rejects_missing_and_invalid_secrets(self):
        self.assertFalse(production_secret_is_safe(""))
        self.assertFalse(production_secret_is_safe("short"))
        self.assertFalse(
            production_secret_is_safe("replace-with-production-secret-min-32-chars")
        )
        self.assertTrue(production_secret_is_safe("n4f7-unique-production-secret-value-32"))

        self.app.config.update(
            {
                "APP_ENV": "production",
                "TESTING": True,
                "SECRET_KEY": "",
                "JWT_SECRET_KEY": "n4f7-unique-production-secret-value-32",
                "STORAGE_PATH": "/tmp/dxcon-p07",
                "CORS_ORIGINS": "https://app.dxcon.test",
                "LOG_FORMAT": "json",
            }
        )
        with self.assertRaises(RuntimeError):
            validate_config(self.app)

        self.app.config["SECRET_KEY"] = "replace-with-production-secret-min-32-chars"
        with self.assertRaises(RuntimeError):
            validate_config(self.app)

    def test_worker_processes_seeded_queue_item(self):
        self.app.config["QUEUE_PROVIDER"] = "memory"
        self.app.extensions.pop("dxcon_queue", None)
        queue = get_queue(self.app)
        queue.enqueue({"type": "noop", "marker": "p07"})
        result = run_worker_cycle(self.app)
        self.assertGreaterEqual(result["broker"]["processed"], 1)
        self.assertEqual(result["role"], "worker")

    def test_scheduler_runs_due_job_once_per_minute(self):
        JobRegistry.initialize()
        JobRegistry.register("p07.noop", lambda: {"ok": True})
        job = ScheduledJob(
            job_code="P07-NOOP",
            name="P07 noop",
            handler="p07.noop",
            cron_expression="* * * * *",
            status="ENABLED",
        )
        db.session.add(job)
        db.session.commit()
        now = datetime(2026, 8, 12, 10, 15, 0)
        first = run_scheduler_cycle(self.app, now=now)
        self.assertIn("P07-NOOP", first["due"])
        self.assertGreaterEqual(ScheduledJobRun.query.filter_by(job_id=job.id).count(), 1)
        second = run_scheduler_cycle(self.app, now=now)
        self.assertEqual(second["due"], [])

    def test_cron_matches_common_expressions(self):
        dt = datetime(2026, 8, 12, 2, 0, 0)
        self.assertTrue(cron_matches("0 2 * * *", dt))
        self.assertFalse(cron_matches("0 3 * * *", dt))
        self.assertTrue(cron_matches("*/15 * * * *", datetime(2026, 8, 12, 10, 30)))
        self.assertFalse(cron_matches("*/15 * * * *", datetime(2026, 8, 12, 10, 31)))

    def test_ready_fails_closed_when_production_redis_missing(self):
        self.app.config.update(
            {
                "APP_ENV": "production",
                "TESTING": True,
                "REDIS_URL": "",
                "QUEUE_PROVIDER": "memory",
            }
        )
        for path in ("/api/v1/system/ready", "/ready"):
            response = self.client.get(path)
            self.assertEqual(response.status_code, 503, path)
            payload = response.get_json()
            self.assertFalse(payload["ready"], path)

    def test_ready_fails_closed_when_production_queue_is_memory(self):
        self.app.config.update(
            {
                "APP_ENV": "production",
                "TESTING": True,
                "REDIS_URL": "redis://localhost:6379/0",
                "QUEUE_PROVIDER": "memory",
            }
        )
        with mock.patch(
            "app.infrastructure.production_readiness.check_redis_health",
            return_value={"status": "OK", "required": True, "mode": "connected", "ok": True},
        ):
            response = self.client.get("/ready")
        self.assertEqual(response.status_code, 503)
        payload = response.get_json()
        self.assertFalse(payload["ready"])
        self.assertEqual(payload.get("queue_provider"), "memory")

    def test_production_config_loader_has_no_silent_unsafe_defaults(self):
        from app.core import config as config_module

        with mock.patch.object(config_module, "_IS_PRODUCTION", True):
            self.assertEqual(
                config_module._env_or(
                    "DXCON_P07_MISSING_SECRET",
                    default="dxcon-dev-secret",
                    production_default="",
                ),
                "",
            )
            self.assertEqual(
                config_module._env_or(
                    "DXCON_P07_MISSING_DB",
                    default="sqlite:///dxcon.db",
                    production_default="",
                ),
                "",
            )
            self.assertEqual(
                config_module._env_or(
                    "DXCON_P07_MISSING_QUEUE",
                    default="memory",
                    production_default="redis",
                ),
                "redis",
            )

    def test_ready_ok_in_development_without_redis(self):
        self.app.config.update({"APP_ENV": "development", "REDIS_URL": "", "QUEUE_PROVIDER": "memory"})
        for path in ("/api/v1/system/ready", "/ready"):
            response = self.client.get(path)
            self.assertEqual(response.status_code, 200, path)
            self.assertTrue(response.get_json()["ready"], path)

    def test_worker_fails_closed_when_production_redis_unavailable(self):
        self.app.config.update(
            {
                "APP_ENV": "production",
                "QUEUE_PROVIDER": "redis",
                "REDIS_URL": "",
                "SQLALCHEMY_DATABASE_URI": "postgresql://dxcon:dxcon@localhost/dxcon",
            }
        )
        with self.assertRaises(RuntimeError):
            run_worker_cycle(self.app)

    def test_migration_022_is_in_ordered_runner(self):
        files = list_migration_files()
        names = [path.name for path in files]
        self.assertIn(IOT_INGEST_SECURITY, names)
        self.assertIn(RECONCILIATION, names)
        self.assertEqual(missing_required_migrations(files), [])
        ordered = ordered_migration_files(files)
        ordered_names = [path.name for path in ordered]
        self.assertEqual(ordered_names[0], RECONCILIATION)
        self.assertEqual(ordered_names[-1], IOT_INGEST_SECURITY)
        self.assertLess(ordered_names.index(RECONCILIATION), ordered_names.index(IOT_INGEST_SECURITY))

    def test_compose_wires_redis_queue_and_healthy_redis(self):
        compose = (ROOT.parent / "docker-compose.production.yml").read_text(encoding="utf-8")
        self.assertIn("QUEUE_PROVIDER: redis", compose)
        self.assertIn("condition: service_healthy", compose)
        self.assertNotIn("placeholder", compose.lower())
        start = (ROOT / "production_start.py").read_text(encoding="utf-8")
        self.assertNotIn("_run_placeholder", start)
        self.assertIn("run_worker_loop", start)
        self.assertIn("run_scheduler_loop", start)


class P07ProductionStartupTestCase(unittest.TestCase):
    def test_worker_and_scheduler_roles_are_not_placeholders(self):
        import production_start

        self.assertFalse(hasattr(production_start, "_run_placeholder"))
        with mock.patch.object(production_start, "_run_worker") as run_worker:
            self.assertEqual(production_start.main(["worker"]), 0)
            run_worker.assert_called_once()
        with mock.patch.object(production_start, "_run_scheduler") as run_scheduler:
            self.assertEqual(production_start.main(["scheduler"]), 0)
            run_scheduler.assert_called_once()


if __name__ == "__main__":
    unittest.main()
