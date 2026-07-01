from flask import Blueprint

from app.models.observability_platform import AuditEvent, ObsAlert, ObsHealthEvent, ObsMetricSnapshot
from app.observability.alert_engine import AlertEngine
from app.observability.audit_service import AuditTimelineService
from app.observability.health_service import HealthPlatformService
from app.observability.metrics_exporter import export_business_payload, export_system_payload
from app.observability.trace_service import TraceService


observability_web_bp = Blueprint("observability_web", __name__)


def _styles():
    return """
    <style>
    body { font-family: Arial, sans-serif; margin: 0; background: #0f172a; color: #e2e8f0; }
    .layout { display: flex; min-height: 100vh; }
    .sidebar { width: 220px; background: #1e293b; padding: 20px; }
    .sidebar a { color: #93c5fd; display: block; margin: 8px 0; text-decoration: none; }
    .sidebar a.active { color: #fff; font-weight: bold; }
    .content { flex: 1; padding: 24px; }
    .card { background: #111827; border: 1px solid #334155; padding: 16px; margin-bottom: 16px; border-radius: 8px; }
    table { width: 100%; border-collapse: collapse; }
    th, td { border-bottom: 1px solid #334155; padding: 8px; text-align: left; }
    </style>
    """


def _sidebar(active):
    links = [
        ("/system/metrics", "Metrics"),
        ("/system/health", "Health"),
        ("/system/alerts", "Alerts"),
        ("/system/audit", "Audit"),
        ("/system/traces", "Traces"),
        ("/system/logs", "Logs"),
    ]
    items = "".join(
        f'<a href="{href}" class="{"active" if href == active else ""}">{label}</a>' for href, label in links
    )
    return f'<div class="sidebar"><h2>Observability</h2>{items}</div>'


@observability_web_bp.route("/system/metrics")
def system_metrics_page():
    from flask import current_app

    metrics = export_system_payload(current_app._get_current_object())
    business = export_business_payload(current_app._get_current_object())
    return f"""<!DOCTYPE html><html><head><title>Metrics</title>{_styles()}</head><body>
    <div class="layout">{_sidebar("/system/metrics")}<div class="content">
    <h1>System Metrics</h1>
    <div class="card">Requests: {metrics.get("requests", {})}<br>Business orders: {business.get("orders_created_total", 0)}</div>
    <div class="card">Snapshots stored: {ObsMetricSnapshot.query.count()}</div>
    </div></div></body></html>"""


@observability_web_bp.route("/system/health")
def system_health_page():
    health = HealthPlatformService.evaluate()
    rows = ObsHealthEvent.query.order_by(ObsHealthEvent.created_at.desc()).limit(10).all()
    table = "".join(
        f"<tr><td>{row.component}</td><td>{row.status}</td></tr>" for row in rows
    )
    return f"""<!DOCTYPE html><html><head><title>Health</title>{_styles()}</head><body>
    <div class="layout">{_sidebar("/system/health")}<div class="content">
    <h1>Health Monitoring</h1>
    <div class="card">Overall status: {health["status"]}</div>
    <table><tr><th>Component</th><th>Status</th></tr>{table or "<tr><td colspan='2'>No events</td></tr>"}</table>
    </div></div></body></html>"""


@observability_web_bp.route("/system/alerts")
def system_alerts_page():
    alerts = AlertEngine.list_alerts(limit=20)
    table = "".join(
        f"<tr><td>{row['alert_code']}</td><td>{row['rule_code']}</td><td>{row['severity']}</td></tr>"
        for row in alerts["alerts"]
    )
    return f"""<!DOCTYPE html><html><head><title>Alerts</title>{_styles()}</head><body>
    <div class="layout">{_sidebar("/system/alerts")}<div class="content">
    <h1>Alert Engine</h1>
    <div class="card">Open alerts: {ObsAlert.query.count()}</div>
    <table><tr><th>Code</th><th>Rule</th><th>Severity</th></tr>{table or "<tr><td colspan='3'>No alerts</td></tr>"}</table>
    </div></div></body></html>"""


@observability_web_bp.route("/system/audit")
def system_audit_page():
    events = AuditTimelineService.list_events(limit=20)
    table = "".join(
        f"<tr><td>{row['event_code']}</td><td>{row['event_type']}</td><td>{row['action']}</td></tr>"
        for row in events["events"]
    )
    return f"""<!DOCTYPE html><html><head><title>Audit</title>{_styles()}</head><body>
    <div class="layout">{_sidebar("/system/audit")}<div class="content">
    <h1>Audit Timeline</h1>
    <div class="card">Events: {AuditEvent.query.count()}</div>
    <table><tr><th>Code</th><th>Type</th><th>Action</th></tr>{table or "<tr><td colspan='3'>No events</td></tr>"}</table>
    </div></div></body></html>"""


@observability_web_bp.route("/system/traces")
def system_traces_page():
    context = TraceService.current_context()
    return f"""<!DOCTYPE html><html><head><title>Traces</title>{_styles()}</head><body>
    <div class="layout">{_sidebar("/system/traces")}<div class="content">
    <h1>Distributed Traces</h1>
    <div class="card">
    Trace ID: {context.get("trace_id")}<br>
    Span ID: {context.get("span_id")}<br>
    Parent Span: {context.get("parent_span_id") or "-"}
    </div></div></div></body></html>"""


@observability_web_bp.route("/system/logs")
def system_logs_page():
    from app.observability.logging_service import StructuredLoggingService

    sample = StructuredLoggingService.log_event("observability", "Dashboard log sample", execution_ms=1.2)
    return f"""<!DOCTYPE html><html><head><title>Logs</title>{_styles()}</head><body>
    <div class="layout">{_sidebar("/system/logs")}<div class="content">
    <h1>Structured Logs</h1>
    <div class="card"><pre>{sample}</pre></div>
    </div></div></body></html>"""
