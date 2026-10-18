"""Focused tests for ScheduledJobRunner retry semantics."""

from __future__ import annotations

import os
import sys
import unittest
from datetime import datetime
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

from app import create_app
from app.extensions.db import db
from app.models.operations_platform import JobExecutionLog, ScheduledJob, ScheduledJobRun
from app.operations.job_lock import JobLockService
from app.operations.job_registry import JobRegistry
from app.operations.job_runner import JobRunner
from app.operations.process_runtime import run_scheduler_cycle
from app.operations.scheduler_service import SchedulerService


class JobRunnerRetryTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()
        JobRegistry._handlers = {}
        self._calls = {"n": 0}

    def tearDown(self):
        JobRegistry._handlers = {}
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def _job(self, *, max_retries, handler="retry.test", code=None):
        job = ScheduledJob(
            job_code=code or f"RETRY-{max_retries}-{id(self)}",
            name="Retry test",
            handler=handler,
            cron_expression="0 0 1 1 *",  # rarely matches in tests
            status="ENABLED",
            max_retries=max_retries,
        )
        db.session.add(job)
        db.session.commit()
        return job

    def test_max_retries_zero_one_attempt_failed(self):
        def always_fail():
            self._calls["n"] += 1
            raise RuntimeError("no-retry")

        JobRegistry.register("retry.test", always_fail)
        job = self._job(max_retries=0)
        result = JobRunner.run_job(job)
        self.assertEqual(result["run"]["status"], "FAILED")
        self.assertEqual(result["run"]["retry_count"], 0)
        self.assertEqual(self._calls["n"], 1)
        run = ScheduledJobRun.query.get(result["run"]["id"])
        self.assertEqual(run.status, "FAILED")
        self.assertIn("no-retry", run.error_message or "")

    def test_max_retries_one_fail_then_success(self):
        def flaky():
            self._calls["n"] += 1
            if self._calls["n"] == 1:
                raise RuntimeError("first")
            return {"ok": True}

        JobRegistry.register("retry.test", flaky)
        job = self._job(max_retries=1)
        result = JobRunner.run_job(job)
        self.assertEqual(result["run"]["status"], "SUCCESS")
        self.assertEqual(result["run"]["retry_count"], 1)
        self.assertEqual(self._calls["n"], 2)
        run = ScheduledJobRun.query.get(result["run"]["id"])
        self.assertEqual(run.status, "SUCCESS")
        self.assertIsNone(run.error_message)
        self.assertEqual(run.retry_count, 1)

    def test_max_retries_one_fail_then_fail(self):
        def always_fail():
            self._calls["n"] += 1
            raise RuntimeError(f"boom-{self._calls['n']}")

        JobRegistry.register("retry.test", always_fail)
        job = self._job(max_retries=1)
        result = JobRunner.run_job(job)
        self.assertEqual(result["run"]["status"], "FAILED")
        self.assertEqual(result["run"]["retry_count"], 1)
        self.assertEqual(self._calls["n"], 2)
        run = ScheduledJobRun.query.get(result["run"]["id"])
        self.assertEqual(run.status, "FAILED")
        self.assertIn("boom-2", run.error_message or "")

    def test_max_retries_greater_than_one(self):
        def flaky():
            self._calls["n"] += 1
            if self._calls["n"] < 4:
                raise RuntimeError(f"fail-{self._calls['n']}")
            return {"ok": True, "attempt": self._calls["n"]}

        JobRegistry.register("retry.test", flaky)
        job = self._job(max_retries=3)
        result = JobRunner.run_job(job)
        self.assertEqual(result["run"]["status"], "SUCCESS")
        self.assertEqual(result["run"]["retry_count"], 3)
        self.assertEqual(self._calls["n"], 4)  # N+1 attempts
        run = ScheduledJobRun.query.get(result["run"]["id"])
        self.assertEqual(run.retry_count, 3)
        self.assertEqual(run.status, "SUCCESS")

    def test_retry_count_persisted_not_local_only(self):
        persisted = []

        def flaky():
            self._calls["n"] += 1
            if self._calls["n"] >= 2:
                row = ScheduledJobRun.query.get(self.run_id)
                persisted.append(row.retry_count)
            if self._calls["n"] < 2:
                raise RuntimeError("once")
            return {"ok": True}

        JobRegistry.register("retry.test", flaky)
        job = self._job(max_retries=2)
        lock = JobLockService.acquire(job.id, timeout_seconds=60)
        run = ScheduledJobRun(
            job_id=job.id,
            run_code="RUN-PERSIST",
            status="RUNNING",
        )
        db.session.add(run)
        db.session.commit()
        self.run_id = run.id
        try:
            JobRunner._execute_attempts(job, run)
        finally:
            JobLockService.release(job.id, lock)

        self.assertEqual(run.status, "SUCCESS")
        self.assertGreaterEqual(len(persisted), 1)
        self.assertEqual(persisted[0], 1)
        db.session.refresh(run)
        self.assertEqual(run.retry_count, 1)

    def test_history_records_every_attempt(self):
        def flaky():
            self._calls["n"] += 1
            if self._calls["n"] < 3:
                raise RuntimeError("x")
            return {"ok": True}

        JobRegistry.register("retry.test", flaky)
        job = self._job(max_retries=2)
        result = JobRunner.run_job(job)
        logs = JobExecutionLog.query.filter_by(run_id=result["run"]["id"]).all()
        messages = [row.message for row in logs]
        self.assertTrue(any("Attempt 1/" in m for m in messages))
        self.assertTrue(any("Attempt 2/" in m for m in messages))
        self.assertTrue(any("Attempt 3/" in m for m in messages))
        self.assertTrue(any("Job failed" in m for m in messages))
        self.assertTrue(any("Job completed" in m for m in messages))

    def test_lock_held_across_retries(self):
        seen = {"blocked": False}

        def flaky():
            self._calls["n"] += 1
            other = JobLockService.acquire(job.id, timeout_seconds=30)
            seen["blocked"] = other is None
            if self._calls["n"] < 2:
                raise RuntimeError("once")
            return {"ok": True}

        JobRegistry.register("retry.test", flaky)
        job = self._job(max_retries=1)
        result = JobRunner.run_job(job)
        self.assertEqual(result["run"]["status"], "SUCCESS")
        self.assertTrue(seen["blocked"])
        token = JobLockService.acquire(job.id, timeout_seconds=30)
        self.assertIsNotNone(token)
        JobLockService.release(job.id, token)

    def test_resume_orphaned_retry_reaches_terminal_state(self):
        def succeed():
            self._calls["n"] += 1
            return {"ok": True}

        JobRegistry.register("retry.test", succeed)
        job = self._job(max_retries=3)
        orphan = ScheduledJobRun(
            job_id=job.id,
            run_code="RUN-ORPHAN1",
            status="RETRY",
            retry_count=1,
            error_message="previous crash",
        )
        db.session.add(orphan)
        db.session.commit()

        with mock.patch(
            "app.operations.process_runtime._require_runtime_dependencies",
            return_value=None,
        ):
            result = run_scheduler_cycle(self.app, now=datetime(2026, 6, 15, 12, 0, 0))

        self.assertGreaterEqual(result["retries"]["retried"], 1)
        db.session.refresh(orphan)
        self.assertIn(orphan.status, {"SUCCESS", "FAILED"})
        self.assertEqual(orphan.status, "SUCCESS")
        # Second cycle must not re-execute the same SUCCESS row forever
        with mock.patch(
            "app.operations.process_runtime._require_runtime_dependencies",
            return_value=None,
        ):
            second = run_scheduler_cycle(self.app, now=datetime(2026, 6, 15, 12, 1, 0))
        self.assertEqual(second["retries"]["candidates"], 0)
        self.assertEqual(self._calls["n"], 1)

    def test_retry_run_compatible_resumes_pending(self):
        def succeed():
            self._calls["n"] += 1
            return {"ok": True}

        JobRegistry.register("retry.test", succeed)
        job = self._job(max_retries=2)
        pending = ScheduledJobRun(
            job_id=job.id,
            run_code="RUN-PEND1",
            status="RETRY",
            retry_count=1,
        )
        db.session.add(pending)
        db.session.commit()
        result = JobRunner.retry_run(job.id)
        self.assertEqual(result["run"]["id"], pending.id)
        self.assertEqual(result["run"]["status"], "SUCCESS")
        self.assertEqual(ScheduledJobRun.query.count(), 1)

    def test_existing_scheduler_service_manual_run_still_works(self):
        def ok():
            return {"ok": True}

        JobRegistry.register("retry.test", ok)
        job = self._job(max_retries=0)
        payload = SchedulerService.run_job(job.id)
        self.assertEqual(payload["run"]["status"], "SUCCESS")


if __name__ == "__main__":
    unittest.main()
