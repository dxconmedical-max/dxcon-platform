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

        started = time.time()
        try:
            JobRegistry.initialize()
            handler = JobRegistry.get(job.handler)
            result = handler()
            run.status = "SUCCESS"
            run.finished_at = datetime.utcnow()
            run.duration_ms = round((time.time() - started) * 1000, 2)
            JobHistoryService.log(job.id, run.id, f"Job completed: {result}")
        except Exception as exc:
            run.status = "FAILED"
            run.error_message = str(exc)
            run.finished_at = datetime.utcnow()
            run.duration_ms = round((time.time() - started) * 1000, 2)
            JobHistoryService.log(job.id, run.id, f"Job failed: {exc}", level="ERROR")
            if run.retry_count < (job.max_retries or 0):
                run.retry_count += 1
                run.status = "RETRY"
        finally:
            db.session.commit()
            JobLockService.release(job.id, lock_token)

        return {"run": run.to_dict(), "job": job.to_dict()}

    @staticmethod
    def retry_run(job_id):
        job = ScheduledJob.query.filter_by(id=job_id).first()
        if job is None:
            raise ValueError("Job not found")
        return JobRunner.run_job(job, manual=True)
