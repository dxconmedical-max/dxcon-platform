import time
import uuid
from datetime import datetime

from app.extensions.db import db
from app.models.operations_platform import ScheduledJob, ScheduledJobRun
from app.operations.job_history import JobHistoryService
from app.operations.job_lock import JobLockService
from app.operations.job_registry import JobRegistry


class JobRunner:
    @staticmethod
    def run_job(job: ScheduledJob, manual=False):
        if job.status == "DISABLED" and not manual:
            raise ValueError("Job is disabled")

        lock_token = JobLockService.acquire(job.id, timeout_seconds=job.timeout_seconds or 300)
        if not lock_token:
            raise ValueError("Job is already running")

        run = ScheduledJobRun(
            job_id=job.id,
            run_code=f"RUN-{uuid.uuid4().hex[:8].upper()}",
            status="RUNNING",
        )
        db.session.add(run)
        db.session.commit()
        JobHistoryService.log(job.id, run.id, f"Job started ({'manual' if manual else 'scheduled'})")

        try:
            return JobRunner._execute_attempts(job, run)
        finally:
            db.session.commit()
            JobLockService.release(job.id, lock_token)

    @staticmethod
    def resume_retry(run: ScheduledJobRun, *, manual=False):
        """Continue a persisted RETRY run on the same ScheduledJobRun row."""
        if run is None or run.status != "RETRY":
            raise ValueError("Retry run not found")

        job = ScheduledJob.query.filter_by(id=run.job_id).first()
        if job is None:
            raise ValueError("Job not found")
        if job.status == "DISABLED" and not manual:
            raise ValueError("Job is disabled")

        lock_token = JobLockService.acquire(job.id, timeout_seconds=job.timeout_seconds or 300)
        if not lock_token:
            raise ValueError("Job is already running")

        JobHistoryService.log(
            job.id,
            run.id,
            f"Resuming retry ({run.retry_count}/{job.max_retries or 0})",
        )
        try:
            return JobRunner._execute_attempts(job, run)
        finally:
            db.session.commit()
            JobLockService.release(job.id, lock_token)

    @staticmethod
    def _execute_attempts(job: ScheduledJob, run: ScheduledJobRun):
        """
        Execute handler with bounded retries on the same ScheduledJobRun.

        Attempt counting:
        - retry_count starts at 0 (persisted on the run row)
        - total attempts allowed = max_retries + 1
        - on failure, if retry_count < max_retries: increment, persist RETRY, try again
        - otherwise persist FAILED
        - success persists SUCCESS (never leaves a failed attempt marked SUCCESS)
        """
        JobRegistry.initialize()
        handler = JobRegistry.get(job.handler)
        max_retries = int(job.max_retries or 0)
        started = time.time()

        while True:
            run.status = "RUNNING"
            db.session.commit()
            attempt_number = int(run.retry_count or 0) + 1
            JobHistoryService.log(
                job.id,
                run.id,
                f"Attempt {attempt_number}/{max_retries + 1}",
            )
            try:
                result = handler()
                run.status = "SUCCESS"
                run.error_message = None
                run.finished_at = datetime.utcnow()
                run.duration_ms = round((time.time() - started) * 1000, 2)
                JobHistoryService.log(job.id, run.id, f"Job completed: {result}")
                db.session.commit()
                return {"run": run.to_dict(), "job": job.to_dict()}
            except Exception as exc:
                run.error_message = str(exc)
                run.finished_at = datetime.utcnow()
                run.duration_ms = round((time.time() - started) * 1000, 2)
                JobHistoryService.log(job.id, run.id, f"Job failed: {exc}", level="ERROR")

                if run.retry_count < max_retries:
                    run.retry_count = int(run.retry_count or 0) + 1
                    run.status = "RETRY"
                    db.session.commit()
                    JobHistoryService.log(
                        job.id,
                        run.id,
                        f"Scheduling retry {run.retry_count}/{max_retries}",
                    )
                    continue

                run.status = "FAILED"
                db.session.commit()
                return {"run": run.to_dict(), "job": job.to_dict()}

    @staticmethod
    def process_pending_retries(limit=20):
        """Resume orphaned RETRY rows; each transitions to SUCCESS or FAILED."""
        rows = (
            ScheduledJobRun.query.filter_by(status="RETRY")
            .order_by(ScheduledJobRun.started_at.asc())
            .limit(int(limit))
            .all()
        )
        completed = 0
        errors = 0
        for run in rows:
            try:
                JobRunner.resume_retry(run)
                # Deterministic terminal state after resume.
                db.session.refresh(run)
                if run.status not in {"SUCCESS", "FAILED"}:
                    run.status = "FAILED"
                    if not run.error_message:
                        run.error_message = "Retry terminated without SUCCESS/FAILED"
                    db.session.commit()
                completed += 1
            except ValueError:
                # Lock held or missing — leave for a later cycle.
                continue
            except Exception:
                errors += 1
                db.session.refresh(run)
                if run.status == "RETRY":
                    # Avoid infinite RETRY pickup on unexpected errors.
                    max_retries = 0
                    job = ScheduledJob.query.filter_by(id=run.job_id).first()
                    if job is not None:
                        max_retries = int(job.max_retries or 0)
                    if int(run.retry_count or 0) >= max_retries:
                        run.status = "FAILED"
                        run.error_message = run.error_message or "Retry processing failed"
                        db.session.commit()
        return {"retried": completed, "errors": errors, "candidates": len(rows)}

    @staticmethod
    def retry_run(job_id):
        """Compatible entry: resume pending RETRY if present, else start a new manual run."""
        job = ScheduledJob.query.filter_by(id=job_id).first()
        if job is None:
            raise ValueError("Job not found")
        pending = (
            ScheduledJobRun.query.filter_by(job_id=job_id, status="RETRY")
            .order_by(ScheduledJobRun.started_at.asc())
            .first()
        )
        if pending is not None:
            return JobRunner.resume_retry(pending, manual=True)
        return JobRunner.run_job(job, manual=True)
