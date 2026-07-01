import json
import uuid

from flask import current_app

from app.extensions.db import db
from app.models.operations_platform import BackupJob, RestoreJob, RestoreValidation
from app.operations.backup_service import OperationsPlatformError


class RestoreService:
    @staticmethod
    def list_restores():
        rows = RestoreJob.query.order_by(RestoreJob.created_at.desc()).all()
        return {"count": len(rows), "restores": [row.to_dict() for row in rows]}

    @staticmethod
    def dry_run(data=None):
        data = data or {}
        backup_id = data.get("backup_id")
        backup = BackupJob.query.filter_by(id=backup_id).first() if backup_id else BackupJob.query.order_by(BackupJob.created_at.desc()).first()
        if backup is None:
            raise OperationsPlatformError("Backup not found", 404)

        app = current_app._get_current_object()
        destructive_allowed = bool(app.config.get("OPS_ALLOW_DESTRUCTIVE_RESTORE", False))
        mode = "DRY_RUN"
        if data.get("mode") == "EXECUTE" and not destructive_allowed:
            mode = "VALIDATION_ONLY"

        restore = RestoreJob(
            restore_code=f"RST-{uuid.uuid4().hex[:8].upper()}",
            backup_job_id=backup.id,
            mode=mode,
            status="VALIDATED" if mode != "EXECUTE" else "BLOCKED",
        )
        db.session.add(restore)
        db.session.flush()

        validation = RestoreValidation(
            restore_job_id=restore.id,
            validation_code=f"VAL-{uuid.uuid4().hex[:8].upper()}",
            status="PASSED",
            detail_json=json.dumps(
                {
                    "mode": mode,
                    "destructive_restore_allowed": destructive_allowed,
                    "message": "Dry-run validation only; no data modified",
                    "backup_code": backup.backup_code,
                }
            ),
        )
        db.session.add(validation)
        db.session.commit()
        return {
            "restore": restore.to_dict(),
            "validation": validation.to_dict(),
            "destructive_restore_allowed": destructive_allowed,
        }
