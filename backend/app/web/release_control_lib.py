"""Release Control web rendering helpers — Phase 5 Sprint 5.12."""

from __future__ import annotations

import html

from app.services import release_control_service as svc
from app.web.demo_pilot_lib import metric_cards, page_header, pilot_styles, status_class

CONTROL_NAV = (
    ("Overview", "/release-control"),
    ("Release History", "/release-control/history"),
    ("Version Compare", "/release-control/version-compare"),
    ("Migration", "/release-control/migration"),
    ("Rollback", "/release-control/rollback"),
    ("Deployment", "/release-control/deployment"),
    ("Audit", "/release-control/audit"),
)


def control_styles() -> str:
    return pilot_styles() + """
    .flow { background:#0f172a; color:#e2e8f0; padding:16px; border-radius:8px; font-family:monospace; line-height:1.6; text-align:center; margin-bottom:16px; font-size:13px; }
    .muted-note { color:#64748b; font-size:13px; margin-bottom:16px; }
    .checklist li { margin-bottom:10px; }
    pre { background:#0f172a; color:#e2e8f0; padding:12px; border-radius:8px; overflow:auto; white-space:pre-wrap; }
    """


def render_control_page(title: str, body_html: str) -> str:
    nav = "".join(f'<a href="{href}">{label}</a>' for label, href in CONTROL_NAV)
    return f"""
    <html>
    <head>
        <title>{title}</title>
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <style>{control_styles()}</style>
    </head>
    <body>
        <div class="wrap">
            <div class="nav">{nav}</div>
            <div class="muted-note">Release lifecycle control · Phase 5 Sprint 5.12</div>
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
            ("History Entries", summary["history_entries"]),
            ("Deployments", summary["deployments_total"]),
            ("Version Diffs", summary["fields_changed"]),
            ("Migration", summary["migration_status"]),
            ("Last Deploy", summary["last_deployment_status"] or "—"),
            ("Audit Entries", summary["audit_entries"]),
        ]
    )
    features = "".join(f"<li>{item}</li>" for item in data["features"])
    flow = """
    Release History → Version Compare → Migration → Rollback → Deployment → Audit
    """
    return f"""
    {page_header("Release Control", "Release history, version diff, migration, rollback, and audit trail.")}
    <div class="flow">{flow}</div>
    {cards}
    <div class="card" style="margin-top:20px;">
        <h3>Sprint 5.12 Features</h3>
        <ul>{features}</ul>
    </div>
    """


def build_history_body() -> str:
    data = svc.release_history()
    rows = [
        [
            str(row.get("sequence", "")),
            html.escape(str(row.get("type", ""))),
            html.escape(str(row.get("version", ""))),
            html.escape(str(row.get("label", ""))),
            html.escape(str(row.get("status", ""))),
            html.escape(str(row.get("generated_at", ""))[:19]),
        ]
        for row in data.get("entries", [])[:20]
    ]
    return f"""
    {page_header("Release History", "Deployments and verification reports.")}
    {metric_cards([
        ("Entries", data["entries_total"]),
        ("Deployments", data["deployments_total"]),
        ("Reports", data["reports_total"]),
    ])}
    <div class="card"><h3>Timeline</h3>{_table(["#", "Type", "Version", "Label", "Status", "When"], rows)}</div>
    """


def build_version_compare_body() -> str:
    data = svc.version_compare()
    rows = [
        [
            html.escape(row["field"]),
            html.escape(str(row["baseline"])),
            html.escape(str(row["current"])),
            "Yes" if row["changed"] else "—",
        ]
        for row in data.get("differences", [])
    ]
    return f"""
    {page_header("Version Compare", f"Baseline: {data.get('baseline_source', '—')}.")}
    {metric_cards([
        ("Fields Changed", data["fields_changed"]),
        ("RC1 Score", data.get("rc1_score", "—")),
    ])}
    <div class="card"><h3>Field Comparison</h3>{_table(["Field", "Baseline", "Current", "Changed"], rows)}</div>
    """


def build_migration_body() -> str:
    data = svc.migration_metrics()
    checks = "".join(
        f'<li><span class="{status_class(item["status"])}">{item["status"]}</span> '
        f'{html.escape(item["title"])} — {html.escape(item["detail"])}</li>'
        for item in data.get("checks", [])
    )
    return f"""
    {page_header("Migration", f"Status: {data.get('status', 'UNKNOWN')}.")}
    {metric_cards([
        ("Checks Passed", f"{data.get('checks_passed', 0)}/{data.get('checks_total', 0)}"),
        ("Tables", data.get("table_count", 0)),
    ])}
    <div class="card"><h3>Migration Checks</h3><ul class="checklist">{checks}</ul></div>
    """


def build_rollback_body() -> str:
    data = svc.rollback_metrics()
    items = "".join(
        f"<li>{html.escape(str(item.get('item', '')))}</li>" for item in data.get("items", [])
    )
    steps = "".join(f"<li>{html.escape(step)}</li>" for step in data.get("pipeline_steps", []))
    return f"""
    {page_header("Rollback", "Rollback plan and pipeline steps.")}
    {metric_cards([("Pipeline Available", "Yes" if data.get("pipeline_available") else "No")])}
    <div class="card"><h3>Checklist</h3><ol class="checklist">{items}</ol></div>
    <div class="card"><h3>Pipeline Steps</h3><ol>{steps}</ol></div>
    """


def build_deployment_body() -> str:
    data = svc.deployment_metrics()
    last = data.get("last_deployment") or {}
    check_rows = [
        [html.escape(row.get("check_code", "")), html.escape(row.get("status", ""))]
        for row in data.get("deployment_checks", [])[:10]
    ]
    return f"""
    {page_header("Deployment", f"Environment: {data.get('environment', '—')}.")}
    {metric_cards([
        ("Version", data.get("current_version", "—")),
        ("Rolling Checks", f"{data.get('rolling_checks_passed', 0)}/{data.get('rolling_checks_total', 0)}"),
        ("Last Status", last.get("status", "—")),
        ("Readiness", last.get("readiness_score", "—")),
    ])}
    <div class="card"><h3>Deployment Checks</h3>{_table(["Check", "Status"], check_rows)}</div>
    """


def build_audit_body() -> str:
    data = svc.release_audit()
    rows = [
        [
            html.escape(str(row.get("created_at", ""))[:19]),
            html.escape(str(row.get("action", ""))),
            html.escape(str(row.get("object_type", ""))),
            html.escape(str(row.get("object_id", ""))),
            html.escape(str(row.get("user_email", ""))),
        ]
        for row in data.get("audit_entries", [])[:20]
    ]
    return f"""
    {page_header("Audit", "Release and deployment audit trail.")}
    {metric_cards([
        ("Entries", data["audit_entries_total"]),
        ("Platform Matched", data["platform_audit_matched"]),
        ("Deployment Records", data["deployment_records_included"]),
    ])}
    <div class="card"><h3>Recent Events</h3>{_table(["When", "Action", "Type", "Object", "Actor"], rows)}</div>
    """
