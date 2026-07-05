"""Operations Runbooks web rendering helpers — Phase 5 Sprint 5.11."""

from __future__ import annotations

import html

from app.services import operations_runbooks_service as svc
from app.web.demo_pilot_lib import metric_cards, page_header, pilot_styles

RUNBOOKS_NAV = (
    ("Overview", "/operations-runbooks"),
    ("Go-Live", "/operations-runbooks/go-live"),
    ("Backup", "/operations-runbooks/backup"),
    ("Restore", "/operations-runbooks/restore"),
    ("Rollback", "/operations-runbooks/rollback"),
    ("Incident", "/operations-runbooks/incident"),
)


def runbooks_styles() -> str:
    return pilot_styles() + """
    .feature-list { font-size:13px; color:#334155; line-height:1.8; }
    pre.runbook { background:#0f172a; color:#e2e8f0; padding:16px; border-radius:8px; overflow:auto; white-space:pre-wrap; font-size:13px; line-height:1.6; max-height:70vh; }
    .muted-note { color:#64748b; font-size:13px; margin-bottom:16px; }
    .links a { margin-right:12px; }
    """


def render_runbooks_page(title: str, body_html: str) -> str:
    nav = "".join(f'<a href="{href}">{label}</a>' for label, href in RUNBOOKS_NAV)
    return f"""
    <html>
    <head>
        <title>{title}</title>
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <style>{runbooks_styles()}</style>
    </head>
    <body>
        <div class="wrap">
            <div class="nav">{nav}</div>
            <div class="muted-note">Operational runbooks · Phase 5 Sprint 5.11</div>
            {body_html}
        </div>
    </body>
    </html>
    """


def _runbook_body(data: dict) -> str:
    sections = "".join(f"<li>{html.escape(section)}</li>" for section in data.get("sections", []))
    content = html.escape(data.get("content", ""))
    return f"""
    {page_header(data["title"], data.get("summary", ""))}
    <div class="card links">
        <strong>{html.escape(data.get("filename", ""))}</strong>
        · {html.escape(data.get("path", ""))}
        · {data.get("size_bytes", 0)} bytes
    </div>
    <div class="card"><h3>Sections</h3><ul>{sections or "<li class='muted'>No sections parsed.</li>"}</ul></div>
    <div class="card"><h3>Content</h3><pre class="runbook">{content or "Runbook file not found."}</pre></div>
    """


def build_dashboard_body() -> str:
    data = svc.dashboard_payload()
    summary = data["summary"]
    cards = metric_cards(
        [
            ("Runbooks", summary["runbooks_total"]),
            ("Present", summary["runbooks_present"]),
            ("Missing", summary["missing_count"]),
        ]
    )
    features = "".join(f"<li>{item}</li>" for item in data["features"])
    links = "".join(
        f'<li><a href="/operations-runbooks/{item["key"].replace("_", "-")}">{html.escape(item["title"])}</a> '
        f'({"OK" if item["exists"] else "MISSING"})</li>'
        for item in data.get("inventory", [])
    )
    return f"""
    {page_header("Operations Runbooks", "Go-live, backup, restore, rollback, and incident procedures.")}
    {cards}
    <div class="card" style="margin-top:20px;">
        <h3>Sprint 5.11 Runbooks</h3>
        <ul class="feature-list">{features}</ul>
    </div>
    <div class="card"><h3>Quick Links</h3><ul class="links">{links}</ul></div>
    """


def build_go_live_body() -> str:
    return _runbook_body(svc.go_live_runbook())


def build_backup_body() -> str:
    return _runbook_body(svc.backup_runbook())


def build_restore_body() -> str:
    return _runbook_body(svc.restore_runbook())


def build_rollback_body() -> str:
    return _runbook_body(svc.rollback_runbook())


def build_incident_body() -> str:
    return _runbook_body(svc.incident_runbook())
