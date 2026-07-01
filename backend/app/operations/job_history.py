from app.extensions.db import db
from app.models.operations_platform import JobExecutionLog


class JobHistoryService:
    @staticmethod
    def log(job_id, run_id, message, level="INFO"):
        row = JobExecutionLog(job_id=job_id, run_id=run_id, level=level, message=message)
        db.session.add(row)
        db.session.commit()
        return row.to_dict()

    @staticmethod
    def list_for_job(job_id, limit=50):
        rows = (
            JobExecutionLog.query.filter_by(job_id=job_id)
            .order_by(JobExecutionLog.created_at.desc())
            .limit(limit)
            .all()
        )
        return [row.to_dict() for row in rows]
