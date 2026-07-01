import uuid
from datetime import datetime, timedelta

from app.extensions.db import db
from app.models.operations_platform import ScheduledJobLock


class JobLockService:
    @staticmethod
    def acquire(job_id, timeout_seconds=300):
        existing = ScheduledJobLock.query.filter_by(job_id=job_id).first()
        now = datetime.utcnow()
        if existing and existing.expires_at and existing.expires_at > now:
            return None
        if existing:
            db.session.delete(existing)
            db.session.commit()
        token = str(uuid.uuid4())
        lock = ScheduledJobLock(
            job_id=job_id,
            lock_token=token,
            expires_at=now + timedelta(seconds=timeout_seconds),
        )
        db.session.add(lock)
        db.session.commit()
        return token

    @staticmethod
    def release(job_id, lock_token):
        lock = ScheduledJobLock.query.filter_by(job_id=job_id, lock_token=lock_token).first()
        if lock:
            db.session.delete(lock)
            db.session.commit()
            return True
        return False
