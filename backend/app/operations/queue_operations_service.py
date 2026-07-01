import uuid

from app.extensions.db import db
from app.models.integration_platform import IntegrationDeadLetter, IntegrationJob
from app.operations.backup_service import OperationsPlatformError


class QueueOperationsService:
    @staticmethod
    def summary():
        queued = IntegrationJob.query.filter(IntegrationJob.status.in_(("QUEUED", "PENDING"))).count()
        failed = IntegrationJob.query.filter_by(status="FAILED").count()
        dead_letters = IntegrationDeadLetter.query.count()
        return {
            "queue_depth": queued,
            "failed_jobs": failed,
            "dead_letter_count": dead_letters,
            "purge_policy": {"enabled": False, "retention_days": 30},
        }

    @staticmethod
    def list_queues():
        return {"queues": [QueueOperationsService.summary()]}

    @staticmethod
    def list_dead_letters(limit=100):
        rows = IntegrationDeadLetter.query.order_by(IntegrationDeadLetter.created_at.desc()).limit(limit).all()
        return {
            "count": len(rows),
            "dead_letters": [row.to_dict() for row in rows],
        }

    @staticmethod
    def retry_failed(limit=10):
        rows = IntegrationJob.query.filter_by(status="FAILED").limit(limit).all()
        retried = 0
        for row in rows:
            row.status = "PENDING"
            row.retry_count = (row.retry_count or 0) + 1
            retried += 1
        db.session.commit()
        return {"retried": retried}

    @staticmethod
    def replay_dead_letter(dead_letter_id):
        row = IntegrationDeadLetter.query.filter_by(id=dead_letter_id).first()
        if row is None:
            raise OperationsPlatformError("Dead letter not found", 404)
        job = IntegrationJob(
            job_code=f"REPLAY-{uuid.uuid4().hex[:8].upper()}",
            adapter_type="REPLAY",
            direction="OUTBOUND",
            status="PENDING",
            payload_json=row.payload_json,
        )
        db.session.add(job)
        db.session.commit()
        return {"replayed": True, "job": job.to_dict(), "dead_letter": row.to_dict()}
