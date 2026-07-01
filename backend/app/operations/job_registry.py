DEFAULT_JOBS = [
    {
        "job_code": "OPS-BACKUP-NIGHTLY",
        "name": "Nightly Database Backup",
        "handler": "backup.database",
        "cron_expression": "0 2 * * *",
    },
    {
        "job_code": "OPS-QUEUE-RETRY",
        "name": "Retry Failed Queue Items",
        "handler": "queue.retry_failed",
        "cron_expression": "*/15 * * * *",
    },
    {
        "job_code": "OPS-SECRET-CHECK",
        "name": "Secret Expiry Check",
        "handler": "secrets.validate",
        "cron_expression": "0 6 * * *",
    },
    {
        "job_code": "OPS-DEPLOY-CHECK",
        "name": "Deployment Readiness Check",
        "handler": "deployment.check",
        "cron_expression": "0 * * * *",
    },
]


class JobRegistry:
    _handlers = {}

    @classmethod
    def register(cls, handler_name, fn):
        cls._handlers[handler_name] = fn

    @classmethod
    def get(cls, handler_name):
        if handler_name not in cls._handlers:
            raise KeyError(f"Unknown job handler: {handler_name}")
        return cls._handlers[handler_name]

    @classmethod
    def list_handlers(cls):
        return sorted(cls._handlers.keys())

    @classmethod
    def initialize(cls):
        if cls._handlers:
            return

        def _backup_handler():
            from app.operations.backup_service import BackupService

            return BackupService.run_backup({"backup_type": "DATABASE"})

        def _queue_retry_handler():
            from app.operations.queue_operations_service import QueueOperationsService

            return QueueOperationsService.retry_failed(limit=5)

        def _secret_validate_handler():
            from app.operations.secret_rotation_service import SecretRotationService

            return SecretRotationService.validate_secrets()

        def _deployment_check_handler():
            from app.operations.deployment_service import DeploymentService

            return DeploymentService.run_checklist()

        cls.register("backup.database", _backup_handler)
        cls.register("queue.retry_failed", _queue_retry_handler)
        cls.register("secrets.validate", _secret_validate_handler)
        cls.register("deployment.check", _deployment_check_handler)
