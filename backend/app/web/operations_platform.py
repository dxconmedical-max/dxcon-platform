from flask import Blueprint

from app.models.operations_platform import (
    BackupArtifact,
    BackupJob,
    MaintenanceWindow,
    ScheduledJob,
    ScheduledJobRun,
    SecretRotationPlan,
)
from app.operations.deployment_service import DeploymentService
from app.operations.maintenance_service import MaintenanceService
from app.operations.queue_operations_service import QueueOperationsService
from app.operations.scheduler_service import SchedulerService


operations_platform_web_bp = Blueprint("operations_platform_web", __name__)


def _styles():
    return """
    <style>
    body { font-family: Arial, sans-serif; margin: 0; background: #111827; color: #f3f4f6; }
    .layout { display: flex; min-height: 100vh; }
    .sidebar { width: 220px; background: #1f2937; padding: 20px; }
    .sidebar a { color: #93c5fd; display: block; margin: 8px 0; text-decoration: none; }
    .sidebar a.active { color: #fff; font-weight: bold; }
    .content { flex: 1; padding: 24px; }
    .card { background: #1f2937; border: 1px solid #374151; padding: 16px; margin-bottom: 16px; border-radius: 8px; }
    table { width: 100%; border-collapse: collapse; }
    th, td { border-bottom: 1px solid #374151; padding: 8px; text-align: left; }
    </style>
    """


def _sidebar(active):
    links = [
        ("/operations", "Overview"),
        ("/operations/jobs", "Jobs"),
        ("/operations/backups", "Backups"),
        ("/operations/maintenance", "Maintenance"),
        ("/operations/secrets", "Secrets"),
        ("/operations/deployment", "Deployment"),
        ("/operations/queues", "Queues"),
    ]
    items = "".join(
        f'<a href="{href}" class="{"active" if href == active else ""}">{label}</a>' for href, label in links
    )
    return f'<div class="sidebar"><h2>Production Ops</h2>{items}</div>'


@operations_platform_web_bp.route("/operations")
def operations_home():
    SchedulerService.ensure_defaults()
    deployment = DeploymentService.current()
    maintenance = MaintenanceService.status()
    queues = QueueOperationsService.summary()
    return f"""<!DOCTYPE html><html><head><title>Operations</title>{_styles()}</head><body>
    <div class="layout">{_sidebar("/operations")}<div class="content">
    <h1>Production Operations Platform</h1>
    <div class="card">Jobs: {ScheduledJob.query.count()} | Backups: {BackupJob.query.count()} | Maintenance active: {bool(maintenance.get("active"))}</div>
    <div class="card">Version: {deployment.get("current_version")} | Queue depth: {queues.get("queue_depth")}</div>
    </div></div></body></html>"""


@operations_platform_web_bp.route("/operations/jobs")
def operations_jobs():
    rows = ScheduledJob.query.order_by(ScheduledJob.job_code.asc()).limit(20).all()
    table = "".join(
        f"<tr><td>{row.job_code}</td><td>{row.name}</td><td>{row.status}</td></tr>" for row in rows
    )
    runs = ScheduledJobRun.query.count()
    return f"""<!DOCTYPE html><html><head><title>Jobs</title>{_styles()}</head><body>
    <div class="layout">{_sidebar("/operations/jobs")}<div class="content">
    <h1>Scheduled Jobs</h1><div class="card">Total runs: {runs}</div>
    <table><tr><th>Code</th><th>Name</th><th>Status</th></tr>{table or "<tr><td colspan='3'>No jobs</td></tr>"}</table>
    </div></div></body></html>"""


@operations_platform_web_bp.route("/operations/backups")
def operations_backups():
    rows = BackupJob.query.order_by(BackupJob.created_at.desc()).limit(20).all()
    table = "".join(
        f"<tr><td>{row.backup_code}</td><td>{row.backup_type}</td><td>{row.status}</td></tr>" for row in rows
    )
    return f"""<!DOCTYPE html><html><head><title>Backups</title>{_styles()}</head><body>
    <div class="layout">{_sidebar("/operations/backups")}<div class="content">
    <h1>Backup & Restore</h1><div class="card">Artifacts: {BackupArtifact.query.count()}</div>
    <table><tr><th>Code</th><th>Type</th><th>Status</th></tr>{table or "<tr><td colspan='3'>No backups</td></tr>"}</table>
    </div></div></body></html>"""


@operations_platform_web_bp.route("/operations/maintenance")
def operations_maintenance():
    status = MaintenanceService.status()
    active = status.get("active")
    banner = status.get("banner", {})
    return f"""<!DOCTYPE html><html><head><title>Maintenance</title>{_styles()}</head><body>
    <div class="layout">{_sidebar("/operations/maintenance")}<div class="content">
    <h1>Maintenance Mode</h1>
    <div class="card">Active: {banner.get("enabled", False)} | Title: {banner.get("title", "-")}</div>
    <div class="card">Scheduled windows: {MaintenanceWindow.query.filter_by(status="SCHEDULED").count()}</div>
    </div></div></body></html>"""


@operations_platform_web_bp.route("/operations/secrets")
def operations_secrets():
    rows = SecretRotationPlan.query.order_by(SecretRotationPlan.secret_name.asc()).limit(20).all()
    table = "".join(
        f"<tr><td>{row.secret_name}</td><td>{row.status}</td><td>{row.fingerprint[:12]}...</td></tr>" for row in rows
    )
    return f"""<!DOCTYPE html><html><head><title>Secrets</title>{_styles()}</head><body>
    <div class="layout">{_sidebar("/operations/secrets")}<div class="content">
    <h1>Secret Rotation</h1>
    <table><tr><th>Name</th><th>Status</th><th>Fingerprint</th></tr>{table or "<tr><td colspan='3'>No plans</td></tr>"}</table>
    </div></div></body></html>"""


@operations_platform_web_bp.route("/operations/deployment")
def operations_deployment():
    deployment = DeploymentService.current()
    record = deployment.get("last_deployment") or {}
    return f"""<!DOCTYPE html><html><head><title>Deployment</title>{_styles()}</head><body>
    <div class="layout">{_sidebar("/operations/deployment")}<div class="content">
    <h1>Deployment Dashboard</h1>
    <div class="card">Version: {deployment.get("current_version")} | SHA: {deployment.get("build_sha")}</div>
    <div class="card">Last deployment status: {record.get("status", "N/A")} | Readiness: {record.get("readiness_score", "N/A")}</div>
    </div></div></body></html>"""


@operations_platform_web_bp.route("/operations/queues")
def operations_queues():
    summary = QueueOperationsService.summary()
    return f"""<!DOCTYPE html><html><head><title>Queues</title>{_styles()}</head><body>
    <div class="layout">{_sidebar("/operations/queues")}<div class="content">
    <h1>Queue Operations</h1>
    <div class="card">Depth: {summary.get("queue_depth")} | Failed: {summary.get("failed_jobs")} | Dead letters: {summary.get("dead_letter_count")}</div>
    </div></div></body></html>"""
