"""Backup & Disaster Recovery web rendering helpers — Phase 5 Sprint 5.3."""

from __future__ import annotations

import html
import json

from app.services import backup_recovery_service as svc
from app.web.demo_pilot_lib import metric_cards, page_header, pilot_styles

BACKUP_NAV = (
    ("Dashboard", "/backup-recovery"),
    ("Scheduler", "/backup-recovery/scheduler"),
    ("Restore", "/backup-recovery/restore"),
    ("PITR", "/backup-recovery/pitr"),
    ("Runbook", "/backup-recovery/runbook"),
)


def backup_styles() -> str:
    return pilot_styles() + """
    .feature-list { font-size:13px; color:#334155; line-height:1.6; }
    pre { background:#0f172a; color:#e2e8f0; padding:12px; border-radius:8px; overflow:auto; white-space:pre-wrap; }
    .muted-note { color:#64748b; font-size:13px; margin-bottom:16px; }
    .checklist li { margin-bottom:10px; }
    """


def render_backup_page(title: str, body_html: str) -> str:
    nav = "".join(f'<a href="{href}">{label}</a>' for label, href in BACKUP_NAV)
    return f"""
    <html>
    <head>
        <title>{title}</title>
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <style>{backup_styles()}</style>
    </head>
    <body>
        <div class="wrap">
            <div class="nav">{nav}</div>
            <div class="muted-note">Backup &amp; disaster recovery · Phase 5 Sprint 5.3</div>
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
            ("Backups", summary["backups_total"]),
            ("Artifacts", summary["artifacts_total"]),
            ("Scheduled Jobs", summary["scheduled_jobs"]),
            ("Restore Validations", summary["restore_validations_passed"]),
            ("PITR Checks", f"{summary['pitr_checklist_passed']}/{summary['pitr_checklist_total']}"),
            ("DR Scripts", summary["deployment_scripts_available"]),
        ]
    )
    features = "".join(f"<li>{item}</li>" for item in data["features"])
    dash = svc.backup_dashboard()
    rows = [
        [
            html.escape(str(item.get("backup_code", ""))),
            html.escape(str(item.get("backup_type", ""))),
            html.escape(str(item.get("status", ""))),
        ]
        for item in dash.get("latest_backups", [])
    ]
    return f"""
    {page_header("Backup Dashboard", "Backup inventory, scheduler, and recovery readiness.")}
    <div class="card"><strong>Status:</strong> {html.escape(data['status'])}</div>
    {cards}
    <div class="card"><h3>Latest Backups</h3>{_table(["Code", "Type", "Status"], rows)}</div>
    <div class="card"><h3>Features</h3><ul class="feature-list">{features}</ul></div>
    """


def build_scheduler_body() -> str:
    data = svc.backup_scheduler()
    rows = [
        [
            html.escape(str(item.get("job_code", ""))),
            html.escape(str(item.get("name", ""))),
            html.escape(str(item.get("cron_expression", ""))),
            html.escape(str(item.get("status", ""))),
        ]
        for item in data.get("scheduled_jobs", [])
    ]
    defaults = "".join(
        f"<li>{html.escape(item['job_code'])} — {html.escape(item['cron_expression'])}</li>"
        for item in data.get("default_jobs", [])
    )
    return f"""
    {page_header("Backup Scheduler", f"Recommended cron: {data.get('recommended_cron')}.")}
    <div class="card"><h3>Default Jobs</h3><ul>{defaults or '<li>No default jobs configured</li>'}</ul></div>
    <div class="card"><h3>Scheduled Backup Jobs</h3>{_table(["Code", "Name", "Cron", "Status"], rows)}</div>
    <div class="card"><p>Trigger manually: <code>{html.escape(data.get('api_trigger', ''))}</code></p></div>
    """


def build_restore_body() -> str:
    data = svc.restore_verification()
    rows = [
        [
            html.escape(str(item.get("validation_code", ""))),
            html.escape(str(item.get("status", ""))),
            html.escape(str(item.get("created_at", ""))),
        ]
        for item in data.get("recent_validations", [])[:15]
    ]
    return f"""
    {page_header("Restore Verification", f"{data.get('validations_passed', 0)} passed validations.")}
    {metric_cards([
        ("Restore Jobs", data.get("restore_jobs_total", 0)),
        ("Validations", data.get("validations_total", 0)),
        ("Passed", data.get("validations_passed", 0)),
    ])}
    <div class="card"><h3>Recent Validations</h3>{_table(["Code", "Status", "Created"], rows)}</div>
    <div class="card"><p>Dry-run API: <code>{html.escape(data.get('dry_run_api', ''))}</code></p></div>
    """


def build_pitr_body() -> str:
    data = svc.pitr_checklist()
    items = []
    for item in data.get("items", []):
        items.append(
            f"<li><strong>{item['id']}. {html.escape(item['title'])}</strong> "
            f"[{html.escape(item['status'])}]<br>{html.escape(item['detail'])}</li>"
        )
    return f"""
    {page_header("PITR Checklist", f"{data.get('items_passed', 0)}/{data.get('items_total', 0)} checks ready.")}
    <div class="card"><p>Engine: {html.escape(str(data.get('database_engine', '')))} · PITR config flag: {data.get('pitr_enabled_config')}</p></div>
    <div class="card"><ol class="checklist">{''.join(items)}</ol></div>
    """


def build_runbook_body() -> str:
    data = svc.disaster_recovery_runbook()
    objectives = data.get("objectives", {})
    api = objectives.get("production_api", {})
    blocks = []
    for scenario in data.get("scenarios", []):
        steps = "".join(f"<li>{html.escape(step)}</li>" for step in scenario.get("steps", []))
        blocks.append(f"<h3>{html.escape(scenario['title'])}</h3><ol>{steps}</ol>")
    docs = ", ".join(
        f"{name}: {'yes' if ok else 'missing'}" for name, ok in data.get("docs_available", {}).items()
    )
    return f"""
    {page_header("Disaster Recovery Runbook", f"Production RTO {api.get('rto_hours', 4)}h / RPO {api.get('rpo_hours', 1)}h.")}
    <div class="card"><p>Documentation: {html.escape(docs)}</p></div>
    <div class="card">{''.join(blocks)}</div>
    <div class="card"><pre>{html.escape(json.dumps(data.get('deployment_scripts', {}), indent=2))}</pre></div>
    """
