"""AI Operations web rendering helpers — Phase 5 Sprint 5.10."""

from __future__ import annotations

import html
import json

from app.services import ai_operations_service as svc
from app.web.demo_pilot_lib import metric_cards, page_header, pilot_styles

AI_OPS_NAV = (
    ("Overview", "/ai-operations"),
    ("Incident Summary", "/ai-operations/incident-summary"),
    ("Usage", "/ai-operations/usage"),
    ("Cost", "/ai-operations/cost"),
    ("Accuracy", "/ai-operations/accuracy"),
    ("Model Health", "/ai-operations/model-health"),
    ("Prompt Version", "/ai-operations/prompt-version"),
)


def ai_ops_styles() -> str:
    return pilot_styles() + """
    .feature-list { columns:2; gap:24px; font-size:13px; color:#334155; }
    pre { background:#0f172a; color:#e2e8f0; padding:12px; border-radius:8px; overflow:auto; white-space:pre-wrap; }
    .muted-note { color:#64748b; font-size:13px; margin-bottom:16px; }
    .flow { background:#0f172a; color:#e2e8f0; padding:16px; border-radius:8px; font-family:monospace; line-height:1.6; text-align:center; margin-bottom:16px; font-size:13px; }
    """


def render_ai_ops_page(title: str, body_html: str) -> str:
    nav = "".join(f'<a href="{href}">{label}</a>' for label, href in AI_OPS_NAV)
    return f"""
    <html>
    <head>
        <title>{title}</title>
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <style>{ai_ops_styles()}</style>
    </head>
    <body>
        <div class="wrap">
            <div class="nav">{nav}</div>
            <div class="muted-note">AI platform observability · Phase 5 Sprint 5.10</div>
            {body_html}
        </div>
    </body>
    </html>
    """


def _table(headers: list[str], rows: list[list[str]]) -> str:
    if not rows:
        return "<p class='muted'>No records in this period.</p>"
    head = "".join(f"<th>{h}</th>" for h in headers)
    body = "".join("<tr>" + "".join(f"<td>{cell}</td>" for cell in row) + "</tr>" for row in rows)
    return f"<table><tr>{head}</tr>{body}</table>"


def build_dashboard_body() -> str:
    data = svc.dashboard_payload()
    summary = data["summary"]
    cards = metric_cards(
        [
            ("AI Requests", summary["ai_requests"]),
            ("Est. Cost (USD)", summary["estimated_cost_usd"]),
            ("Success Rate %", summary["success_rate_percent"]),
            ("Degraded Models", summary["providers_degraded"]),
            ("Prompts", summary["prompts_total"]),
            ("Failed Jobs", summary["failed_inference_jobs"]),
        ]
    )
    features = "".join(f"<li>{item}</li>" for item in data["features"])
    flow = """
    AI Incident Summary → AI Usage → AI Cost → AI Accuracy → Model Health → Prompt Version
    """
    return f"""
    {page_header("AI Operations", "Platform usage, cost, accuracy, and model observability.")}
    <div class="flow">{flow}</div>
    {cards}
    <div class="card" style="margin-top:20px;">
        <h3>Sprint 5.10 Features</h3>
        <ul class="feature-list">{features}</ul>
    </div>
    """


def build_incident_summary_body() -> str:
    data = svc.ai_incident_summary()
    summary = data["summary"]
    job_rows = [
        [row.get("job_code", ""), row.get("status", ""), row.get("provider_id", "")]
        for row in data.get("failed_jobs", [])[:10]
    ]
    return f"""
    {page_header("AI Incident Summary", f"Status: {data['status']}.")}
    {metric_cards([
        ("Failed Jobs", summary["failed_inference_jobs"]),
        ("Audit Errors", summary["audit_error_events"]),
        ("AI Incidents", summary["ai_incidents"]),
    ])}
    <div class="card"><h3>Failed Inference Jobs</h3>{_table(["Job", "Status", "Provider"], job_rows)}</div>
    """


def build_usage_body() -> str:
    data = svc.ai_usage_metrics()
    totals = data["usage"]["totals"]
    rows = [
        [task, str(bucket["requests"]), str(bucket["tokens_in"]), str(bucket["tokens_out"])]
        for task, bucket in sorted(totals.get("by_task_type", {}).items())
    ]
    return f"""
    {page_header("AI Usage", f"Period {data['period_start']} to {data['period_end']}.")}
    {metric_cards([
        ("Requests", totals.get("requests", 0)),
        ("Tokens In", totals.get("tokens_in", 0)),
        ("Tokens Out", totals.get("tokens_out", 0)),
        ("Interpretation Rate %", data.get("interpretation_rate_percent", 0)),
    ])}
    <div class="card"><h3>By Task Type</h3>{_table(["Task", "Requests", "Tokens In", "Tokens Out"], rows)}</div>
    """


def build_cost_body() -> str:
    data = svc.ai_cost_metrics()
    totals = data["totals"]
    rows = [
        [row["task_type"], str(row["requests"]), f"${row['estimated_cost_usd']:.4f}"]
        for row in data.get("by_task_type", [])[:10]
    ]
    return f"""
    {page_header("AI Cost", data["pricing"]["note"])}
    {metric_cards([
        ("Total Cost (USD)", totals["estimated_cost_usd"]),
        ("Input Cost", totals["input_cost_usd"]),
        ("Output Cost", totals["output_cost_usd"]),
        ("Requests", totals["requests"]),
    ])}
    <div class="card"><h3>Cost by Task</h3>{_table(["Task", "Requests", "Est. Cost"], rows)}</div>
    """


def build_accuracy_body() -> str:
    data = svc.ai_accuracy_metrics()
    rows = [[status, str(count)] for status, count in sorted(data.get("by_status", {}).items())]
    return f"""
    {page_header("AI Accuracy", f"Period {data['period_start']} to {data['period_end']}.")}
    {metric_cards([
        ("Success Rate %", data["success_rate_percent"]),
        ("Failure Rate %", data["failure_rate_percent"]),
        ("Human Review %", data["human_review_completion_percent"]),
        ("Jobs Total", data["jobs_total"]),
    ])}
    <div class="card"><h3>Job Status</h3>{_table(["Status", "Count"], rows)}</div>
    """


def build_model_health_body() -> str:
    data = svc.model_health_metrics()
    rows = [
        [
            html.escape(row["name"]),
            html.escape(row["model_name"]),
            row["health"],
            f"{row['success_rate_percent']:.1f}%",
            str(row["failures_in_period"]),
        ]
        for row in data.get("models", [])[:15]
    ]
    return f"""
    {page_header("Model Health", f"Platform: {data['platform_status']}.")}
    {metric_cards([
        ("Providers", data["providers_total"]),
        ("Degraded", data["providers_degraded"]),
    ])}
    <div class="card"><h3>Provider Health</h3>{_table(["Provider", "Model", "Health", "Success %", "Failures"], rows)}</div>
    """


def build_prompt_version_body() -> str:
    data = svc.prompt_version_metrics()
    rows = [
        [
            html.escape(row["prompt_code"]),
            html.escape(row["name"]),
            str(row["active_version"]),
            str(row["versions_total"]),
            html.escape(row.get("active_template_preview", "")),
        ]
        for row in data.get("prompts", [])[:15]
    ]
    return f"""
    {page_header("Prompt Version", f"Registry: {data.get('registry_api', '')}")}
    {metric_cards([("Prompts", data["prompts_total"])])}
    <div class="card"><h3>Active Prompt Versions</h3>{_table(["Code", "Name", "Active Ver.", "Versions", "Preview"], rows)}</div>
    """
