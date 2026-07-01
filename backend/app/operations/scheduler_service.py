import json
import uuid

from app.extensions.db import db
from app.models.operations_platform import ScheduledJob, ScheduledJobRun
from app.operations.job_history import JobHistoryService
from app.operations.job_registry import DEFAULT_JOBS, JobRegistry
from app.operations.job_runner import JobRunner


class OperationsPlatformError(Exception):
    def __init__(self, message, status_code=400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class SchedulerService:
    @staticmethod
    def ensure_defaults():
        JobRegistry.initialize()
        if ScheduledJob.query.first():
            return {"seeded": False}
        for item in DEFAULT_JOBS:
            db.session.add(
                ScheduledJob(
                    job_code=item["job_code"],
                    name=item["name"],
                    handler=item["handler"],
                    cron_expression=item["cron_expression"],
                    status="ENABLED",
                )
            )
        db.session.commit()
        return {"seeded": True}

    @staticmethod
    def list_jobs():
        rows = ScheduledJob.query.order_by(ScheduledJob.job_code.asc()).all()
        return {"count": len(rows), "jobs": [row.to_dict() for row in rows], "handlers": JobRegistry.list_handlers()}

    @staticmethod
    def get_job(job_id):
        row = ScheduledJob.query.filter_by(id=job_id).first()
        if row is None:
            raise OperationsPlatformError("Job not found", 404)
        payload = row.to_dict()
        payload["runs"] = [
            item.to_dict()
            for item in ScheduledJobRun.query.filter_by(job_id=job_id).order_by(ScheduledJobRun.started_at.desc()).limit(10).all()
        ]
        payload["logs"] = JobHistoryService.list_for_job(job_id)
        return payload

    @staticmethod
    def create_job(data):
        if not data.get("name") or not data.get("handler"):
            raise OperationsPlatformError("name and handler are required")
        JobRegistry.initialize()
        if data["handler"] not in JobRegistry.list_handlers():
            raise OperationsPlatformError(f"Unknown handler: {data['handler']}")
        row = ScheduledJob(
            job_code=data.get("job_code") or f"JOB-{uuid.uuid4().hex[:8].upper()}",
            name=data["name"],
            handler=data["handler"],
            cron_expression=data.get("cron_expression"),
            status=data.get("status") or "ENABLED",
            timeout_seconds=int(data.get("timeout_seconds") or 300),
            max_retries=int(data.get("max_retries") or 3),
            config_json=json.dumps(data.get("config") or {}),
        )
        db.session.add(row)
        db.session.commit()
        return row.to_dict()

    @staticmethod
    def run_job(job_id):
        job = ScheduledJob.query.filter_by(id=job_id).first()
        if job is None:
            raise OperationsPlatformError("Job not found", 404)
        try:
            return JobRunner.run_job(job, manual=True)
        except ValueError as exc:
            raise OperationsPlatformError(str(exc), 409)

    @staticmethod
    def enable_job(job_id):
        return SchedulerService._set_status(job_id, "ENABLED")

    @staticmethod
    def disable_job(job_id):
        return SchedulerService._set_status(job_id, "DISABLED")

    @staticmethod
    def list_runs(job_id):
        job = ScheduledJob.query.filter_by(id=job_id).first()
        if job is None:
            raise OperationsPlatformError("Job not found", 404)
        rows = ScheduledJobRun.query.filter_by(job_id=job_id).order_by(ScheduledJobRun.started_at.desc()).all()
        return {"count": len(rows), "runs": [row.to_dict() for row in rows], "logs": JobHistoryService.list_for_job(job_id)}

    @staticmethod
    def _set_status(job_id, status):
        job = ScheduledJob.query.filter_by(id=job_id).first()
        if job is None:
            raise OperationsPlatformError("Job not found", 404)
        job.status = status
        db.session.commit()
        return job.to_dict()
