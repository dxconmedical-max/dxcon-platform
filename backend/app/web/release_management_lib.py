"""Release Management web rendering helpers — Phase 5 Sprint 5.7."""

from __future__ import annotations

import html

from app.services import release_management_service as svc
from app.web.demo_pilot_lib import metric_cards, page_header, pilot_styles, status_class

RELEASE_NAV = (
    ("Overview", "/release-management"),
    ("Environment", "/release-management/environment"),
    ("Version", "/release-management/version"),
    ("Release Notes", "/release-management/notes"),
    ("Migration", "/release-management/migration"),
    ("Health", "/release-management/health"),
    ("Rollback", "/release-management/rollback"),
)


def release_styles() -> str:
    return pilot_styles() + """
    .flow { background:#0f172a; color:#e2e8f0; padding:16px; border-radius:8px; font-family:monospace; line-height:1.8; text-align:center; margin-bottom:16px; }
    .muted { color:#64748b; font-size:13px; margin-bottom:16px; }
    .checklist li { margin-bottom:10px; }
    pre { background:#0f172a; color:#e2e8f0; padding:12px; border-radius:8px; overflow:auto; white-space:pre-wrap; }
    """


def render_release_page(title: str, body_html: str) -> str:
    nav = "".join(f'<a href="{href}">{label}</a>' for label, href in RELEASE_NAV)
    return f"""
    <html>
    <head>
        <title>{title}</title>
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <style>{release_styles()}</style>
    </head>
    <body>
        <div class="wrap">
            <div class="nav">{nav}</div>
            <div class="muted">Platform release operations · Phase 5 Sprint 5.7</div>
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


def _release_flow() -> str:
    return """
    <div class="flow">
        Environment<br>
        ↓<br>
        Version<br>
        ↓<br>
        Release Notes<br>
        ↓<br>
        Migration Status<br>
        ↓<br>
        Health<br>
        ↓<br>
        Rollback
    </div>
    """


def build_dashboard_body() -> str:
    data = svc.dashboard_payload()
    summary = data["summary"]
    cards = metric_cards(
        [
            ("Environment", summary["environment"]),
            ("Version", summary["version"]),
            ("Migration", summary["migration_status"]),
            ("Health", summary["health_status"]),
            ("Release Notes", summary["release_notes_count"]),
            ("Git SHA", summary["git_sha"][:12] if summary.get("git_sha") else "local"),
        ]
    )
    features = "".join(f"<li>{item}</li>" for item in data["features"])
    return f"""
    {page_header("Release Management", "Environment through rollback for controlled platform releases.")}
    {_release_flow()}
    <div class="card"><strong>Status:</strong> <span class="{status_class(data['status'])}">{html.escape(data['status'])}</span></div>
    {cards}
    <div class="card"><h3>Features</h3><ul>{features}</ul></div>
    """


def build_environment_body() -> str:
    data = svc.release_environment()
    rows = [
        ["APP_ENV", html.escape(str(data.get("app_env", "")))],
        ["Runtime Profile", html.escape(str(data.get("runtime_profile", "")))],
        ["Provider", html.escape(str(data.get("provider", "")))],
        ["Database", html.escape(str(data.get("database_uri_prefix", "")))],
        ["Deploy Score", str(data.get("deployment_score", ""))],
        ["Production Ready", "Yes" if data.get("ready_for_production") else "Review"],
    ]
    return f"""
    {page_header("Environment", "Runtime profile and deployment readiness context.")}
    <div class="card">{_table(["Setting", "Value"], rows)}</div>
    <div class="card"><h3>Legacy API</h3><pre>{html.escape(data.get('legacy_api', ''))}</pre></div>
    """


def build_version_body() -> str:
    data = svc.release_version()
    rows = [
        ["Version", html.escape(str(data.get("version", "")))],
        ["Git SHA", html.escape(str(data.get("git_sha", "")))],
        ["Build Time", html.escape(str(data.get("build_time", "")))],
        ["Service", html.escape(str(data.get("service", "")))],
        ["Environment", html.escape(str(data.get("environment", "")))],
    ]
    deployment = data.get("last_deployment") or {}
    if deployment:
        rows.append(["Last Deployment", html.escape(str(deployment.get("deployment_code", "")))])
    return f"""
    {page_header("Version", "Build traceability for release promotion and rollback.")}
    <div class="card">{_table(["Field", "Value"], rows)}</div>
    """


def build_notes_body() -> str:
    data = svc.release_notes()
    rows = [
        [
            html.escape(str(note.get("version", ""))),
            html.escape(str(note.get("title", ""))),
            html.escape(str(note.get("summary", ""))[:100]),
        ]
        for note in data.get("notes", [])
    ]
    return f"""
    {page_header("Release Notes", "RC and sprint verification summaries for the platform.")}
    <div class="card"><p>Current version: <strong>{html.escape(str(data.get('current_version', '')))}</strong></p></div>
    <div class="card"><h3>Notes</h3>{_table(["Version", "Title", "Summary"], rows)}</div>
    """


def build_migration_body() -> str:
    data = svc.migration_status()
    checks = "".join(
        f"<li><strong>{html.escape(item['title'])}</strong> [{html.escape(item['status'])}]</li>"
        for item in data.get("checks", [])
    )
    missing = ", ".join(data.get("missing_core_tables", [])) or "None"
    return f"""
    {page_header("Migration Status", "Schema readiness before and after release cutover.")}
    <div class="card"><p>Status: <strong>{html.escape(str(data.get('status', '')))}</strong></p>
    <p>Tables: {data.get('table_count', 0)} · Missing core: {html.escape(missing)}</p></div>
    <div class="card"><h3>Checks</h3><ul class="checklist">{checks}</ul></div>
    """


def build_health_body() -> str:
    data = svc.release_health()
    rows = [
        [html.escape(data["live"]["path"]), str(data["live"]["status_code"]), html.escape(str(data["live"]["payload"].get("status", "")))],
        [html.escape(data["ready"]["path"]), str(data["ready"]["status_code"]), html.escape(str(data["ready"]["payload"].get("status", "")))],
        [html.escape(data["health"]["path"]), str(data["health"]["status_code"]), html.escape(str(data["health"]["payload"].get("status", "")))],
    ]
    return f"""
    {page_header("Health", "Live, ready, and health probes for release verification.")}
    <div class="card"><h3>Probes</h3>{_table(["Path", "Code", "Status"], rows)}</div>
    <div class="card"><p>Infrastructure: {html.escape(str(data.get('infrastructure_status', '')))}</p></div>
    """


def build_rollback_body() -> str:
    data = svc.release_rollback()
    items = "".join(
        f"<li>{html.escape(str(item.get('item', '')))}</li>" for item in data.get("items", [])
    )
    steps = "".join(f"<li>{html.escape(step)}</li>" for step in data.get("pipeline_steps", []))
    return f"""
    {page_header("Rollback", "Controlled rollback plan when a release must be reversed.")}
    <div class="card"><h3>Checklist</h3><ol class="checklist">{items}</ol></div>
    <div class="card"><h3>Pipeline Steps</h3><ol class="checklist">{steps}</ol></div>
    <div class="card"><h3>Legacy API</h3><pre>{html.escape(data.get('legacy_api', ''))}</pre></div>
    """
