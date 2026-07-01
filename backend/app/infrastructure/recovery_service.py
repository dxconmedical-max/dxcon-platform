import json
import uuid

from flask import current_app

from app.extensions.db import db
from app.models.infrastructure_readiness import RecoveryArtifact, RecoveryPlan, RecoveryReport, RecoveryTest
from app.operations.backup_service import BackupService
from app.operations.restore_service import RestoreService


class RecoveryService:
    @staticmethod
    def ensure_defaults():
        if RecoveryPlan.query.first():
            return {"seeded": False}
        plan = RecoveryPlan(
            plan_code="DR-PRIMARY",
            name="Primary Disaster Recovery Plan",
            rto_minutes=60,
            rpo_minutes=15,
            detail_json=json.dumps({"scope": "database_and_storage"}),
        )
        db.session.add(plan)
        db.session.commit()
        return {"seeded": True}

    @staticmethod
    def list_plans():
        rows = RecoveryPlan.query.order_by(RecoveryPlan.plan_code.asc()).all()
        return {"count": len(rows), "plans": [row.to_dict() for row in rows]}

    @staticmethod
    def validate_backup():
        backup = BackupService.run_backup({"backup_type": "FULL"})
        validation = BackupService.validate_backup(backup["backup"]["id"])
        return {"backup": backup, "validation": validation}

    @staticmethod
    def validate_restore():
        return RestoreService.dry_run({})

    @staticmethod
    def run_recovery_test(plan_id=None, mode="DRY_RUN"):
        plan = RecoveryPlan.query.filter_by(id=plan_id).first() if plan_id else RecoveryPlan.query.first()
        if plan is None:
            RecoveryService.ensure_defaults()
            plan = RecoveryPlan.query.first()
        backup_validation = RecoveryService.validate_backup()
        restore_validation = RecoveryService.validate_restore()
        test = RecoveryTest(
            plan_id=plan.id,
            test_code=f"RT-{uuid.uuid4().hex[:8].upper()}",
            status="PASSED",
            mode=mode,
        )
        artifact = RecoveryArtifact(
            plan_id=plan.id,
            artifact_code=f"RA-{uuid.uuid4().hex[:8].upper()}",
            artifact_type="BACKUP_MANIFEST",
            checksum=backup_validation["backup"]["artifact"]["checksum"],
            storage_path=backup_validation["backup"]["artifact"]["storage_path"],
        )
        report = RecoveryReport(
            plan_id=plan.id,
            report_code=f"RR-{uuid.uuid4().hex[:8].upper()}",
            status="COMPLETED",
            summary_json=json.dumps(
                {
                    "rto_minutes": plan.rto_minutes,
                    "rpo_minutes": plan.rpo_minutes,
                    "backup_valid": backup_validation["validation"]["valid"],
                    "restore_mode": restore_validation["restore"]["mode"],
                }
            ),
        )
        db.session.add(test)
        db.session.add(artifact)
        db.session.add(report)
        db.session.commit()
        return {
            "plan": plan.to_dict(),
            "test": test.to_dict(),
            "artifact": artifact.to_dict(),
            "report": report.to_dict(),
            "backup_validation": backup_validation,
            "restore_validation": restore_validation,
        }

    @staticmethod
    def summary():
        return {
            "plans": RecoveryPlan.query.count(),
            "tests": RecoveryTest.query.count(),
            "artifacts": RecoveryArtifact.query.count(),
            "reports": RecoveryReport.query.count(),
        }
