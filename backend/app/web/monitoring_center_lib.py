"""Monitoring Center web rendering helpers — Phase 5 Sprint 5.2."""

from __future__ import annotations

import html
import json

from app.services import monitoring_center_service as svc
from app.web.demo_pilot_lib import metric_cards, page_header, pilot_styles

MONITORING_NAV = (
    ("Overview", "/monitoring"),
    ("Application", "/monitoring/application"),
    ("Queues", "/monitoring/queues"),
    ("Database", "/monitoring/database"),
    ("Redis", "/monitoring/redis"),
    ("Latency", "/monitoring/latency"),
    ("Errors", "/monitoring/errors"),
    ("Jobs", "/monitoring/jobs"),
    ("Business KPI", "/monitoring/kpi"),
    ("Alerts", "/monitoring/alerts"),
)


def monitoring_styles() -> str:
    return pilot_styles() + """
    .feature-list { columns:2; gap:24px; font-size:13px; color:#334155; }
    pre { background:#0f172a; color:#e2e8f0; padding:12px; border-radius:8px; overflow:auto; max-width:100%; white-space:pre-wrap; }
    .muted-note { color:#64748b; font-size:13px; margin-bottom:16px; }
    .status-ok { color:#047857; font-weight:700; }
    .status-warn { color:#b45309; font-weight:700; }
    .status-down { color:#b91c1c; font-weight:700; }
    """


def _status_class(status: str) -> str:
    normalized = (status or "").upper()
    if normalized == "OK":
        return "status-ok"
    if normalized == "DOWN":
        return "status-down"
    return "status-warn"


def render_monitoring_page(title: str, body_html: str) -> str:
    nav = "".join(f'<a href="{href}">{label}</a>' for label, href in MONITORING_NAV)
    return f"""
    <html>
    <head>
        <title>{title}</title>
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <style>{monitoring_styles()}</style>
    </head>
    <body>
        <div class="wrap">
            <div class="nav">{nav}</div>
            <div class="muted-note">Operations monitoring · Phase 5 Sprint 5.2</div>
            {body_html}
        </div>
    </body>
    </html>
    """


def _table(headers: list[str], rows: list[list[str]]) -> str:
    if not rows:
        return "<p class='muted'>No records.</p>"
    head = "".join(f"<th>{h}</th>" for h in headers)
    body = "".join("<tr>" + "".join(f"<td>{cell}</td>" for cell in row) + "</tr>" for row in rows)
    return f"<table><tr>{head}</tr>{body}</table>"


def build_dashboard_body() -> str:
    data = svc.dashboard_payload()
    summary = data["summary"]
    cards = metric_cards(
        [
            ("App Status", summary["application_status"]),
            ("Queue Depth", summary["queue_depth"]),
            ("DB Status", summary["database_status"]),
            ("Redis", summary["redis_status"]),
            ("Avg Latency (ms)", summary["average_latency_ms"]),
            ("Error Rate %", summary["error_rate_percent"]),
            ("Open Alerts", summary["open_alerts"]),
            ("Scheduled Jobs", summary["scheduled_jobs"]),
        ]
    )
    features = "".join(f"<li>{item}</li>" for item in data["features"])
    return f"""
    {page_header("Monitoring Center", "Application, infrastructure, and business observability.")}
    <div class="card"><strong>Status:</strong> <span class="{_status_class(data['status'])}">{html.escape(data['status'])}</span></div>
    {cards}
    <div class="card" style="margin-top:20px;">
        <h3>Monitoring Views</h3>
        <ul class="feature-list">{features}</ul>
    </div>
    """


def build_application_body() -> str:
    data = svc.application_health()
    rows = [
        [
            html.escape(item.get("component", "")),
            html.escape(str(item.get("status", ""))),
        ]
        for item in data.get("components", [])
    ]
    return f"""
    {page_header("Application Health", f"Overall status {data.get('status')}.")}
    <div class="card">{_table(["Component", "Status"], rows)}</div>
    """


def build_queues_body() -> str:
    data = svc.queue_health()
    summary = data.get("summary", {})
    return f"""
    {page_header("Queue Health", f"Status {data.get('status')}.")}
    {metric_cards([
        ("Queue Depth", summary.get("queue_depth", 0)),
        ("Failed Jobs", summary.get("failed_jobs", 0)),
        ("Dead Letters", summary.get("dead_letter_count", 0)),
    ])}
    """


def build_database_body() -> str:
    data = svc.database_health()
    return f"""
    {page_header("Database Health", f"Engine {html.escape(str(data.get('engine', '')))}.")}
    {metric_cards([
        ("Status", data.get("status", "UNKNOWN")),
        ("Connectivity", data.get("connectivity", "UNKNOWN")),
        ("Migrations Ready", data.get("migrations", {}).get("ready", False)),
    ])}
    """


def build_redis_body() -> str:
    data = svc.redis_health()
    return f"""
    {page_header("Redis Health", f"Configured: {'Yes' if data.get('configured') else 'No'}.")}
    {metric_cards([
        ("Status", data.get("status", "UNKNOWN")),
        ("Ping OK", data.get("ping", {}).get("ok", False)),
    ])}
    <div class="card"><pre>{html.escape(json.dumps(data.get("ping", {}), indent=2))}</pre></div>
    """


def build_latency_body() -> str:
    data = svc.api_latency_metrics()
    return f"""
    {page_header("API Latency", "HTTP request latency from observability metrics.")}
    {metric_cards([
        ("Average (ms)", data.get("average_ms", 0)),
        ("P95 (ms)", data.get("p95_ms", 0)),
        ("Samples", data.get("count", 0)),
    ])}
    """


def build_errors_body() -> str:
    data = svc.error_rate_metrics()
    return f"""
    {page_header("Error Rate", "HTTP and authentication failure rates.")}
    {metric_cards([
        ("Error Rate %", data.get("error_rate_percent", 0)),
        ("HTTP Errors", data.get("errors_total", 0)),
        ("Requests", data.get("requests_total", 0)),
        ("Auth Failures", data.get("authentication_failures", 0)),
    ])}
    """


def build_jobs_body() -> str:
    data = svc.background_jobs_status()
    runner = data.get("runner", {})
    rows = [
        [
            html.escape(str(item.get("job_code", ""))),
            html.escape(str(item.get("status", ""))),
            html.escape(str(item.get("handler", ""))),
        ]
        for item in data.get("scheduled_jobs", [])[:15]
    ]
    return f"""
    {page_header("Background Jobs", "In-process runner and scheduled jobs.")}
    {metric_cards([
        ("Runner Pending", runner.get("pending", 0)),
        ("Runner Failed", runner.get("failed", 0)),
        ("Scheduled Jobs", data.get("scheduled_jobs_total", 0)),
        ("Enabled", data.get("scheduled_jobs_enabled", 0)),
    ])}
    <div class="card"><h3>Scheduled Jobs</h3>{_table(["Code", "Status", "Handler"], rows)}</div>
    """


def build_kpi_body() -> str:
    data = svc.business_kpi_snapshot()
    obs = data.get("observability", {})
    return f"""
    {page_header("Business KPI", "Runtime counters and KPI engine snapshot.")}
    {metric_cards([
        ("Orders", obs.get("orders_created_total", 0)),
        ("Results Approved", obs.get("results_approved_total", 0)),
        ("Critical Results", obs.get("critical_results_total", 0)),
        ("Notification Latency (ms)", obs.get("notification_latency_ms", 0)),
    ])}
    <div class="card"><h3>KPI Engine</h3><pre>{html.escape(json.dumps(data.get("kpi_engine", {}), indent=2, default=str)[:4000])}</pre></div>
    """


def build_alerts_body() -> str:
    data = svc.alerts_overview(limit=30)
    rows = [
        [
            html.escape(str(item.get("rule_code", ""))),
            html.escape(str(item.get("severity", ""))),
            html.escape(str(item.get("status", ""))),
            html.escape(str(item.get("message", ""))[:80]),
        ]
        for item in data.get("alerts", [])[:20]
    ]
    return f"""
    {page_header("Alerts", f"{data.get('open_alerts', 0)} open of {data.get('alerts_total', 0)} total.")}
    <div class="card">{_table(["Rule", "Severity", "Status", "Message"], rows)}</div>
    """
