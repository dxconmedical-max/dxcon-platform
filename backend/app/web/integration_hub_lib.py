"""Integration Hub web rendering helpers."""

from __future__ import annotations

import json

from flask import session

from app.services import integration_hub_service as svc
from app.web.demo_pilot_lib import metric_cards, page_header, pilot_styles

HUB_NAV = (
    ("Dashboard", "/integration-hub"),
    ("Connectors", "/integration-hub/connectors"),
    ("Adapters", "/integration-hub/adapters"),
    ("Webhooks", "/integration-hub/webhooks"),
    ("API Keys", "/integration-hub/api-keys"),
    ("Retry Queue", "/integration-hub/retry-queue"),
    ("Dead Letters", "/integration-hub/dead-letters"),
    ("Audit Log", "/integration-hub/audit"),
    ("Sandbox", "/integration-hub/sandbox"),
)


def hub_styles() -> str:
    return pilot_styles() + """
    .actions a, .actions button { margin-right:8px; margin-bottom:8px; }
    .btn { background:#0f766e; color:white; border:none; padding:8px 14px; border-radius:8px; cursor:pointer; text-decoration:none; font-size:13px; }
    .btn-secondary { background:#64748b; }
    .form-grid label { display:block; font-size:13px; color:#475569; margin-bottom:4px; }
    .form-grid input, .form-grid select, .form-grid textarea { width:100%; max-width:520px; padding:10px; border:1px solid #cbd5e1; border-radius:8px; margin-bottom:12px; }
    .flash { background:#ecfdf5; border:1px solid #86efac; color:#166534; padding:12px 16px; border-radius:10px; margin-bottom:16px; }
    .error { background:#fef2f2; border:1px solid #fecaca; color:#991b1b; padding:12px 16px; border-radius:10px; margin-bottom:16px; }
    .feature-list { columns:2; gap:24px; font-size:13px; color:#334155; }
    pre { background:#0f172a; color:#e2e8f0; padding:12px; border-radius:8px; overflow:auto; max-width:100%; }
    """


def render_hub_page(title: str, body_html: str) -> str:
    nav = "".join(f'<a href="{href}">{label}</a>' for label, href in HUB_NAV)
    actor = session.get("email", "Admin")
    return f"""
    <html>
    <head>
        <title>{title}</title>
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <style>{hub_styles()}</style>
    </head>
    <body>
        <div class="wrap">
            <div class="nav">{nav}</div>
            <div class="muted" style="margin-bottom:14px;">Signed in as {actor} · Phase 4 Sprint 4.1</div>
            {body_html}
        </div>
    </body>
    </html>
    """


def _table(headers: list[str], rows: list[list[str]]) -> str:
    if not rows:
        return "<p class='muted'>No records.</p>"
    head = "".join(f"<th>{h}</th>" for h in headers)
    body = ""
    for row in rows:
        body += "<tr>" + "".join(f"<td>{cell}</td>" for cell in row) + "</tr>"
    return f"<table><tr>{head}</tr>{body}</table>"


def build_dashboard_body(*, message: str = "", error: str = "") -> str:
    data = svc.dashboard_payload()
    summary = data["summary"]
    cards = metric_cards(
        [
            ("Connectors", summary["connectors"]),
            ("Adapters", summary["adapters"]),
            ("Webhooks", summary["webhooks"]),
            ("API Keys", summary["api_keys"]),
            ("Retry Queue", summary["retry_queue"]),
            ("Dead Letters", summary["dead_letters"]),
            ("Audit Entries", summary["audit_entries"]),
        ]
    )
    features = "".join(f"<li>{item}</li>" for item in data["features"])
    flash = ""
    if message:
        flash = f'<div class="flash">{message}</div>'
    if error:
        flash = f'<div class="error">{error}</div>'
    return f"""
    {flash}
    {page_header("Integration Center", "Enterprise integration hub for HIS, LIS, EMR, ERP, Insurance, and Payment.")}
    {cards}
    <div class="card" style="margin-top:20px;">
        <h3>Sprint 4.1 Features</h3>
        <ul class="feature-list">{features}</ul>
    </div>
    """


def build_connectors_body() -> str:
    data = svc.list_connectors()
    rows = [
        [
            row.get("connector_code", ""),
            row.get("name", ""),
            row.get("adapter_type", ""),
            row.get("status", ""),
        ]
        for row in data["connectors"]
    ]
    return f"""
    {page_header("Connector Registry", f"{data['count']} registered connectors.")}
    {_table(["Code", "Name", "Adapter", "Status"], rows)}
    """


def build_adapters_body() -> str:
    data = svc.list_adapters()
    rows = [
        [row.get("type", ""), row.get("vendor", ""), "Yes" if row.get("connected") else "No"]
        for row in data["adapters"]
    ]
    return f"""
    {page_header("Adapter Registry", f"{data['count']} adapters loaded.")}
    {_table(["Type", "Vendor", "Connected"], rows)}
    """


def build_webhooks_body() -> str:
    data = svc.list_webhooks()
    rows = [
        [
            row.get("endpoint_code", ""),
            row.get("name", ""),
            row.get("target_url", ""),
            row.get("status", ""),
        ]
        for row in data.get("webhooks", [])
    ]
    return f"""
    {page_header("Webhook Manager", f"{data['count']} webhook endpoints.")}
    {_table(["Code", "Name", "Target URL", "Status"], rows)}
    """


def build_api_keys_body() -> str:
    data = svc.list_api_keys()
    rows = [
        [
            row.get("key_prefix", ""),
            row.get("client_id", ""),
            row.get("status", ""),
            row.get("created_at", ""),
        ]
        for row in data.get("keys", [])
    ]
    return f"""
    {page_header("API Key Manager", f"{data['count']} API keys.")}
    {_table(["Prefix", "Client", "Status", "Created"], rows)}
    """


def build_retry_queue_body() -> str:
    data = svc.list_retry_queue()
    rows = [
        [
            row.get("job_code", ""),
            row.get("adapter_type", ""),
            row.get("status", ""),
            str(row.get("retry_count", 0)),
        ]
        for row in data.get("jobs", [])
    ]
    return f"""
    {page_header("Retry Queue", f"{data['count']} pending or failed jobs.")}
    {_table(["Job", "Adapter", "Status", "Retries"], rows)}
    """


def build_dead_letters_body() -> str:
    data = svc.list_dead_letters()
    rows = [
        [
            row.get("id", "")[:8],
            row.get("job_id", "")[:8],
            row.get("reason", "")[:80],
        ]
        for row in data.get("dead_letters", [])
    ]
    return f"""
    {page_header("Dead Letter Queue", f"{data['count']} dead letter entries.")}
    {_table(["DLQ ID", "Job ID", "Reason"], rows)}
    """


def build_audit_body() -> str:
    data = svc.list_audit(page_size=50)
    rows = [
        [
            row.get("action", ""),
            row.get("resource_type", ""),
            row.get("resource_id", "") or "",
            row.get("actor", ""),
            row.get("created_at", ""),
        ]
        for row in data.get("entries", [])
    ]
    return f"""
    {page_header("Integration Audit Log", f"{data['count']} audit entries.")}
    {_table(["Action", "Resource", "Resource ID", "Actor", "Created"], rows)}
    """


def build_sandbox_body(*, result: dict | None = None, error: str = "") -> str:
    options = "".join(f'<option value="{t}">{t}</option>' for t in svc.SUPPORTED_ADAPTERS)
    flash = f'<div class="error">{error}</div>' if error else ""
    result_html = ""
    if result:
        result_html = f"<h3>Sandbox Result</h3><pre>{json.dumps(result, indent=2, default=str)}</pre>"
    return f"""
    {flash}
    {page_header("Sandbox Test Endpoint", "Run non-destructive adapter sandbox tests.")}
    <form method="POST" class="form-grid card">
        <label for="adapter_type">Adapter Type</label>
        <select id="adapter_type" name="adapter_type">{options}</select>
        <label for="payload">Payload JSON (optional)</label>
        <textarea id="payload" name="payload" rows="6" placeholder='{{"patient_id": "TEST-001"}}'></textarea>
        <button class="btn" type="submit">Run Sandbox Test</button>
    </form>
    {result_html}
    """
