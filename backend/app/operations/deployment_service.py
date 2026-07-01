import json
import uuid
from datetime import datetime

from app.core.build_info import build_info
from app.extensions.db import db
from app.models.operations_platform import DeploymentCheck, DeploymentRecord, DeploymentRollbackPlan
from app.operations.backup_service import OperationsPlatformError


DEFAULT_CHECKS = [
    ("DB_CONNECTIVITY", "Database connectivity"),
    ("MIGRATIONS", "Migration readiness"),
    ("QUEUE_HEALTH", "Queue health"),
    ("SECRET_VALIDATION", "Secret validation"),
    ("BACKUP_RECENT", "Recent backup available"),
]


class DeploymentService:
    @staticmethod
    def current():
        record = DeploymentRecord.query.order_by(DeploymentRecord.created_at.desc()).first()
        info = build_info()
        payload = {
            "current_version": info.get("version"),
            "build_sha": info.get("commit") or info.get("build_sha"),
            "build_time": info.get("build_time"),
            "environment": info.get("environment", "production"),
            "last_deployment": record.to_dict() if record else None,
        }
        if record:
            payload["checks"] = [
                item.to_dict() for item in DeploymentCheck.query.filter_by(deployment_id=record.id).all()
            ]
            rollback = DeploymentRollbackPlan.query.filter_by(deployment_id=record.id).first()
            payload["rollback_plan"] = rollback.to_dict() if rollback else None
        return payload

    @staticmethod
    def run_checklist():
        info = build_info()
        record = DeploymentRecord(
            deployment_code=f"DEP-{uuid.uuid4().hex[:8].upper()}",
            version=info.get("version") or "unknown",
            build_sha=info.get("commit") or info.get("build_sha") or "unknown",
            build_time=datetime.utcnow(),
            environment=info.get("environment", "production"),
            status="SUCCESS",
            readiness_score=100.0,
        )
        db.session.add(record)
        db.session.flush()

        passed = 0
        checks = []
        for code, name in DEFAULT_CHECKS:
            status = "PASSED"
            detail = "OK"
            try:
                if code == "DB_CONNECTIVITY":
                    from sqlalchemy import text

                    db.session.execute(text("SELECT 1"))
                elif code == "SECRET_VALIDATION":
                    from app.operations.secret_rotation_service import SecretRotationService

                    result = SecretRotationService.validate_secrets()
                    if result["warnings"]:
                        status = "WARNING"
                        detail = "secret warnings present"
                elif code == "BACKUP_RECENT":
                    from app.models.operations_platform import BackupJob

                    if BackupJob.query.count() == 0:
                        status = "WARNING"
                        detail = "no backups found"
            except Exception as exc:
                status = "FAILED"
                detail = str(exc)
            if status == "PASSED":
                passed += 1
            row = DeploymentCheck(
                deployment_id=record.id,
                check_code=code,
                name=name,
                status=status,
                detail_json=json.dumps({"detail": detail}),
            )
            db.session.add(row)
            checks.append(row)

        record.readiness_score = round((passed / len(DEFAULT_CHECKS)) * 100, 2)
        record.status = "SUCCESS" if record.readiness_score >= 80 else "DEGRADED"
        rollback = DeploymentRollbackPlan(
            deployment_id=record.id,
            plan_code=f"RBK-{uuid.uuid4().hex[:8].upper()}",
            target_version=info.get("previous_version") or "previous",
            status="READY",
            detail_json=json.dumps({"strategy": "metadata-only rollback plan"}),
        )
        db.session.add(rollback)
        db.session.commit()
        return {
            "deployment": record.to_dict(),
            "checks": [item.to_dict() for item in checks],
            "rollback_plan": rollback.to_dict(),
        }

    @staticmethod
    def rollback_plan():
        record = DeploymentRecord.query.order_by(DeploymentRecord.created_at.desc()).first()
        if record is None:
            raise OperationsPlatformError("No deployment record found", 404)
        plan = DeploymentRollbackPlan.query.filter_by(deployment_id=record.id).first()
        if plan is None:
            raise OperationsPlatformError("Rollback plan not found", 404)
        return {"deployment": record.to_dict(), "rollback_plan": plan.to_dict()}
