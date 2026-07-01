from datetime import datetime, timedelta

from app.extensions.db import db
from app.models.integration_platform import IntegrationDeadLetter, IntegrationJob
from app.models.operations_platform import (
    BackupArtifact,
    BackupJob,
    DeploymentCheck,
    DeploymentRecord,
    DeploymentRollbackPlan,
    JobExecutionLog,
    MaintenanceWindow,
    RestoreJob,
    ScheduledJobRun,
    SecretRotationEvent,
)
from app.operations.backup_service import BackupService
from app.operations.deployment_service import DeploymentService
from app.operations.maintenance_service import MaintenanceService
from app.operations.scheduler_service import SchedulerService
from app.operations.secret_rotation_service import SecretRotationService


def seed_operations_demo():
    SchedulerService.ensure_defaults()
    SecretRotationService.ensure_defaults()

    if ScheduledJobRun.query.count() >= 5:
        return {
            "seeded": False,
            "jobs": SchedulerService.list_jobs()["count"],
            "backups": BackupJob.query.count(),
        }

    jobs = SchedulerService.list_jobs()["jobs"]
    for job in jobs[:2]:
        from app.models.operations_platform import ScheduledJob

        row = ScheduledJob.query.filter_by(id=job["id"]).first()
        if row:
            from app.operations.job_runner import JobRunner

            try:
                JobRunner.run_job(row, manual=True)
            except Exception:
                pass

    BackupService.run_backup({"backup_type": "DATABASE"})
    BackupService.run_backup({"backup_type": "STORAGE"})
    DeploymentService.run_checklist()

    MaintenanceService.schedule(
        {
            "title": "Planned DB maintenance",
            "message": "Read-only mode expected",
            "starts_at": (datetime.utcnow() + timedelta(days=2)).isoformat(),
            "ends_at": (datetime.utcnow() + timedelta(days=2, hours=2)).isoformat(),
        }
    )

    from app.models.operations_platform import SecretRotationPlan

    plan = SecretRotationPlan.query.first()
    if plan:
        SecretRotationService.mark_rotated(plan.id)

    if IntegrationJob.query.count() == 0:
        job = IntegrationJob(
            job_code="OPS-DEMO-FAILED",
            adapter_type="DEMO",
            direction="OUTBOUND",
            status="FAILED",
            payload_json='{"demo": true}',
        )
        db.session.add(job)
        db.session.flush()
        db.session.add(
            IntegrationDeadLetter(
                job_id=job.id,
                reason="Demo dead letter",
                payload_json='{"demo": true}',
            )
        )
        db.session.commit()

    return {
        "seeded": True,
        "jobs": SchedulerService.list_jobs()["count"],
        "runs": ScheduledJobRun.query.count(),
        "backups": BackupJob.query.count(),
        "artifacts": BackupArtifact.query.count(),
        "maintenance_windows": MaintenanceWindow.query.count(),
        "secret_events": SecretRotationEvent.query.count(),
        "deployments": DeploymentRecord.query.count(),
        "checks": DeploymentCheck.query.count(),
        "rollback_plans": DeploymentRollbackPlan.query.count(),
        "restores": RestoreJob.query.count(),
        "logs": JobExecutionLog.query.count(),
        "dead_letters": IntegrationDeadLetter.query.count(),
    }


if __name__ == "__main__":
    from app import create_app

    app = create_app()
    with app.app_context():
        db.create_all()
        print(seed_operations_demo())
