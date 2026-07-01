from flask import Blueprint, request

from app.operations.backup_service import BackupService, OperationsPlatformError
from app.operations.deployment_service import DeploymentService
from app.operations.maintenance_service import MaintenanceService
from app.operations.queue_operations_service import QueueOperationsService
from app.operations.restore_service import RestoreService
from app.operations.scheduler_service import SchedulerService
from app.operations.secret_rotation_service import SecretRotationService


def _error(exc):
    return {"error": exc.message}, exc.status_code


operations_bp = Blueprint("operations_platform", __name__, url_prefix="/api/v1/operations")


@operations_bp.route("/jobs", methods=["GET"])
def list_jobs():
    SchedulerService.ensure_defaults()
    return SchedulerService.list_jobs()


@operations_bp.route("/jobs", methods=["POST"])
def create_job():
    try:
        return SchedulerService.create_job(request.get_json(silent=True) or {}), 201
    except OperationsPlatformError as exc:
        return _error(exc)


@operations_bp.route("/jobs/<job_id>", methods=["GET"])
def get_job(job_id):
    try:
        return SchedulerService.get_job(job_id)
    except OperationsPlatformError as exc:
        return _error(exc)


@operations_bp.route("/jobs/<job_id>/run", methods=["POST"])
def run_job(job_id):
    try:
        return SchedulerService.run_job(job_id)
    except OperationsPlatformError as exc:
        return _error(exc)


@operations_bp.route("/jobs/<job_id>/enable", methods=["POST"])
def enable_job(job_id):
    try:
        return SchedulerService.enable_job(job_id)
    except OperationsPlatformError as exc:
        return _error(exc)


@operations_bp.route("/jobs/<job_id>/disable", methods=["POST"])
def disable_job(job_id):
    try:
        return SchedulerService.disable_job(job_id)
    except OperationsPlatformError as exc:
        return _error(exc)


@operations_bp.route("/jobs/<job_id>/runs", methods=["GET"])
def list_job_runs(job_id):
    try:
        return SchedulerService.list_runs(job_id)
    except OperationsPlatformError as exc:
        return _error(exc)


@operations_bp.route("/backups", methods=["GET"])
def list_backups():
    return BackupService.list_backups()


@operations_bp.route("/backups/run", methods=["POST"])
def run_backup():
    try:
        return BackupService.run_backup(request.get_json(silent=True) or {}), 201
    except OperationsPlatformError as exc:
        return _error(exc)


@operations_bp.route("/backups/<backup_id>", methods=["GET"])
def get_backup(backup_id):
    try:
        return BackupService.get_backup(backup_id)
    except OperationsPlatformError as exc:
        return _error(exc)


@operations_bp.route("/backups/<backup_id>/validate", methods=["POST"])
def validate_backup(backup_id):
    try:
        return BackupService.validate_backup(backup_id)
    except OperationsPlatformError as exc:
        return _error(exc)


@operations_bp.route("/restores", methods=["GET"])
def list_restores():
    return RestoreService.list_restores()


@operations_bp.route("/restores/dry-run", methods=["POST"])
def restore_dry_run():
    try:
        return RestoreService.dry_run(request.get_json(silent=True) or {}), 201
    except OperationsPlatformError as exc:
        return _error(exc)


@operations_bp.route("/maintenance", methods=["GET"])
def maintenance_status():
    return MaintenanceService.status()


@operations_bp.route("/maintenance/enable", methods=["POST"])
def maintenance_enable():
    return MaintenanceService.enable(request.get_json(silent=True) or {}), 200


@operations_bp.route("/maintenance/disable", methods=["POST"])
def maintenance_disable():
    return MaintenanceService.disable()


@operations_bp.route("/maintenance/schedule", methods=["POST"])
def maintenance_schedule():
    try:
        return MaintenanceService.schedule(request.get_json(silent=True) or {}), 201
    except OperationsPlatformError as exc:
        return _error(exc)


@operations_bp.route("/secrets", methods=["GET"])
def list_secrets():
    SecretRotationService.ensure_defaults()
    return SecretRotationService.list_secrets()


@operations_bp.route("/secrets/validate", methods=["POST"])
def validate_secrets():
    return SecretRotationService.validate_secrets()


@operations_bp.route("/secrets/rotation-plan", methods=["POST"])
def create_rotation_plan():
    try:
        return SecretRotationService.create_rotation_plan(request.get_json(silent=True) or {}), 201
    except OperationsPlatformError as exc:
        return _error(exc)


@operations_bp.route("/secrets/<plan_id>/mark-rotated", methods=["POST"])
def mark_secret_rotated(plan_id):
    try:
        return SecretRotationService.mark_rotated(plan_id, request.get_json(silent=True) or {})
    except OperationsPlatformError as exc:
        return _error(exc)


@operations_bp.route("/deployment", methods=["GET"])
def deployment_status():
    return DeploymentService.current()


@operations_bp.route("/deployment/check", methods=["POST"])
def deployment_check():
    return DeploymentService.run_checklist(), 201


@operations_bp.route("/deployment/rollback-plan", methods=["GET"])
def deployment_rollback_plan():
    try:
        return DeploymentService.rollback_plan()
    except OperationsPlatformError as exc:
        return _error(exc)


@operations_bp.route("/queues", methods=["GET"])
def queue_summary():
    return QueueOperationsService.list_queues()


@operations_bp.route("/queues/dead-letters", methods=["GET"])
def queue_dead_letters():
    return QueueOperationsService.list_dead_letters()


@operations_bp.route("/queues/dead-letters/<dead_letter_id>/replay", methods=["POST"])
def replay_dead_letter(dead_letter_id):
    try:
        return QueueOperationsService.replay_dead_letter(dead_letter_id)
    except OperationsPlatformError as exc:
        return _error(exc)
