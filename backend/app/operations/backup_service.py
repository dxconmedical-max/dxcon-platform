import hashlib
import json
import uuid
from datetime import datetime

from flask import current_app

from app.extensions.db import db
from app.models.operations_platform import BackupArtifact, BackupJob, RestoreValidation
from app.operations.backup_registry import BACKUP_TYPES


class OperationsPlatformError(Exception):
    def __init__(self, message, status_code=400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class BackupService:
    @staticmethod
    def list_backups():
        rows = BackupJob.query.order_by(BackupJob.created_at.desc()).all()
        items = []
        for row in rows:
            payload = row.to_dict()
            payload["artifacts"] = [
                artifact.to_dict()
                for artifact in BackupArtifact.query.filter_by(backup_job_id=row.id).all()
            ]
            items.append(payload)
        return {"count": len(items), "backups": items, "backup_types": list(BACKUP_TYPES)}

    @staticmethod
    def get_backup(backup_id):
        row = BackupJob.query.filter_by(id=backup_id).first()
        if row is None:
            raise OperationsPlatformError("Backup not found", 404)
        payload = row.to_dict()
        payload["artifacts"] = [
            artifact.to_dict() for artifact in BackupArtifact.query.filter_by(backup_job_id=row.id).all()
        ]
        return payload

    @staticmethod
    def run_backup(data=None):
        data = data or {}
        backup_type = (data.get("backup_type") or "DATABASE").upper()
        if backup_type not in BACKUP_TYPES:
            raise OperationsPlatformError(f"Invalid backup type: {backup_type}")

        app = current_app._get_current_object()
        db_uri = app.config.get("SQLALCHEMY_DATABASE_URI", "sqlite://")
        manifest = {
            "backup_type": backup_type,
            "database_uri_prefix": db_uri.split(":", 1)[0],
            "created_at": datetime.utcnow().isoformat(),
            "tables_estimate": "metadata-only",
        }
        checksum_source = json.dumps(manifest, sort_keys=True)
        checksum = hashlib.sha256(checksum_source.encode()).hexdigest()

        job = BackupJob(
            backup_code=f"BKP-{uuid.uuid4().hex[:8].upper()}",
            backup_type=backup_type,
            status="COMPLETED",
            manifest_json=json.dumps(manifest),
            retention_days=int(data.get("retention_days") or 30),
        )
        db.session.add(job)
        db.session.flush()

        artifact = BackupArtifact(
            backup_job_id=job.id,
            artifact_code=f"ART-{uuid.uuid4().hex[:8].upper()}",
            storage_path=f"/var/backups/dxcon/{job.backup_code}.manifest",
            checksum=checksum,
            size_bytes=len(checksum_source),
        )
        db.session.add(artifact)
        db.session.commit()
        return {"backup": job.to_dict(), "artifact": artifact.to_dict(), "manifest": manifest}

    @staticmethod
    def validate_backup(backup_id):
        row = BackupJob.query.filter_by(id=backup_id).first()
        if row is None:
            raise OperationsPlatformError("Backup not found", 404)
        artifacts = BackupArtifact.query.filter_by(backup_job_id=row.id).all()
        valid = all(artifact.checksum for artifact in artifacts)
        validation = RestoreValidation(
            restore_job_id=None,
            validation_code=f"VAL-{uuid.uuid4().hex[:8].upper()}",
            status="PASSED" if valid else "FAILED",
            detail_json=json.dumps({"backup_id": backup_id, "artifact_count": len(artifacts)}),
        )
        db.session.add(validation)
        db.session.commit()
        return {"valid": valid, "validation": validation.to_dict(), "backup": row.to_dict()}
