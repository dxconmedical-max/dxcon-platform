"""Partner Developer Portal web rendering helpers — Phase 4 Sprint 4.5."""

from __future__ import annotations

import html
import json

from app.services import developer_portal_service as svc
from app.web.demo_pilot_lib import metric_cards, page_header, pilot_styles

DEV_NAV = (
    ("Overview", "/developer"),
    ("API Docs", "/developer/api"),
    ("Webhooks", "/developer/webhooks"),
    ("Sandbox", "/developer/sandbox"),
    ("Onboarding", "/developer/onboarding"),
    ("API Keys", "/developer/api-keys"),
    ("Routes", "/developer/routes"),
    ("Swagger", "/api-docs/swagger"),
)


def dev_styles() -> str:
    return pilot_styles() + """
    .btn { background:#0b4f6c; color:white; border:none; padding:8px 14px; border-radius:8px; cursor:pointer; font-size:13px; }
    .form-grid label { display:block; font-size:13px; color:#475569; margin-bottom:4px; }
    .form-grid input, .form-grid textarea, .form-grid select {
        width:100%; max-width:520px; padding:10px; border:1px solid #cbd5e1; border-radius:8px; margin-bottom:12px;
    }
    .error { background:#fef2f2; border:1px solid #fecaca; color:#991b1b; padding:12px 16px; border-radius:10px; margin-bottom:16px; }
    .success { background:#ecfdf5; border:1px solid #a7f3d0; color:#065f46; padding:12px 16px; border-radius:10px; margin-bottom:16px; }
    .feature-list { columns:2; gap:24px; font-size:13px; color:#334155; }
    pre { background:#0f172a; color:#e2e8f0; padding:12px; border-radius:8px; overflow:auto; max-width:100%; white-space:pre-wrap; }
    .link-list a { display:block; margin:6px 0; color:#1d4ed8; }
    .checklist li { margin-bottom:10px; line-height:1.5; }
    """


def dev_sidebar(active: str) -> str:
    items = "".join(
        f'<a href="{href}" class="{"active" if href == active else ""}">{label}</a>'
        for label, href in DEV_NAV
    )
    return f'<div class="sidebar"><h2>Developer Portal</h2>{items}</div>'


def legacy_dev_sidebar(active: str) -> str:
    """Sidebar for legacy api_platform pages (api-keys, routes)."""
    return f"""
    <style>
    body {{ font-family: Arial, sans-serif; margin: 0; background: #f4f6f8; color: #1f2933; }}
    .layout {{ display: flex; min-height: 100vh; }}
    .sidebar {{ width: 240px; background: #102a43; color: #fff; padding: 20px; }}
    .sidebar a {{ color: #d9e2ec; display: block; margin: 8px 0; text-decoration: none; }}
    .sidebar a.active {{ color: #fff; font-weight: bold; }}
    .content {{ flex: 1; padding: 24px; }}
    table {{ width: 100%; border-collapse: collapse; background: #fff; }}
    th, td {{ border: 1px solid #d9e2ec; padding: 8px; text-align: left; vertical-align: top; }}
    .card {{ background: #fff; padding: 16px; margin-bottom: 16px; border: 1px solid #d9e2ec; }}
    </style>
    {dev_sidebar(active)}
    """


def render_dev_page(title: str, body_html: str, *, legacy_layout: bool = False) -> str:
    if legacy_layout:
        return f"""<!DOCTYPE html><html><head><title>{title}</title></head><body>
        <div class="layout">{body_html}</div></body></html>"""

    nav = "".join(f'<a href="{href}">{label}</a>' for label, href in DEV_NAV)
    return f"""
    <html>
    <head>
        <title>{title}</title>
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <style>{dev_styles()}</style>
    </head>
    <body>
        <div class="wrap">
            <div class="nav">{nav}</div>
            <div class="muted" style="margin-bottom:14px;">Partner Developer Portal · Phase 4 Sprint 4.5</div>
            {body_html}
        </div>
    </body>
    </html>
    """


def build_landing_body(app) -> str:
    data = svc.dashboard_payload(app)
    summary = data["summary"]
    cards = metric_cards(
        [
            ("API Routes", summary["routes_total"]),
            ("Domains", summary["domains_total"]),
            ("Active Keys", summary["active_api_keys"]),
            ("Webhooks", summary["webhooks"]),
            ("SDK Languages", summary["sdk_languages"]),
            ("Onboarding Steps", data["onboarding_steps"]),
        ]
    )
    features = "".join(f"<li>{item}</li>" for item in data["features"])
    docs = data["documentation"]
    doc_links = "".join(
        f'<li><a href="{href}">{label}</a></li>'
        for label, href in (
            ("OpenAPI JSON", docs["openapi_json"]),
            ("Swagger UI", docs["swagger_ui"]),
            ("ReDoc", docs["redoc"]),
            ("API Hub", docs["developer_api"]),
        )
    )
    return f"""
    {page_header("Partner Developer Portal", "Understand, test, and onboard DxCon integrations.")}
    <div class="card"><strong>Platform status:</strong> {html.escape(data["status"])}</div>
    {cards}
    <div class="card" style="margin-top:20px;">
        <h3>Quick Links</h3>
        <ul class="link-list">{doc_links}</ul>
    </div>
    <div class="card">
        <h3>Sprint 4.5 Features</h3>
        <ul class="feature-list">{features}</ul>
    </div>
    """


def build_api_body() -> str:
    docs = svc.api_documentation_links()
    keys = svc.api_key_instructions()
    sdk = svc.sdk_download_links()
    postman = svc.postman_collection_link()
    doc_rows = [
        ["OpenAPI JSON", docs["openapi_json"]],
        ["OpenAPI YAML", docs["openapi_yaml"]],
        ["Swagger UI", docs["swagger_ui"]],
        ["ReDoc", docs["redoc"]],
        ["Docs Index", docs["docs_index"]],
    ]
    doc_table = "".join(
        f'<tr><td>{label}</td><td><a href="{href}">{href}</a></td></tr>' for label, href in doc_rows
    )
    steps = "".join(f"<li>{html.escape(step)}</li>" for step in keys["steps"])
    sdk_links = "".join(
        f'<li><a href="{item["url"]}">{item["language"]} — {item["filename"]}</a></li>'
        for item in sdk["downloads"]
    ) or "<li>No generated SDK files found.</li>"
    return f"""
    {page_header("API Documentation & Credentials", "Reference docs, keys, SDKs, and Postman starter collection.")}
    <div class="card">
        <h3>API Documentation</h3>
        <table><tr><th>Resource</th><th>Link</th></tr>{doc_table}</table>
    </div>
    <div class="card">
        <h3>API Key Instructions</h3>
        <p>Send credentials using the <code>{html.escape(keys["header"])}</code> header.</p>
        <ol>{steps}</ol>
        <p>Active keys in this environment: <strong>{keys["active_keys"]}</strong></p>
        <p><a href="{keys["manage_ui"]}">Manage API keys</a></p>
    </div>
    <div class="card">
        <h3>SDK Downloads</h3>
        <ul class="link-list">{sdk_links}</ul>
    </div>
    <div class="card">
        <h3>Postman Collection</h3>
        <p><a href="{postman["collection_url"]}">Download Postman collection JSON</a></p>
        <p>Or import OpenAPI directly: <a href="{postman["openapi_import"]}">{postman["openapi_import"]}</a></p>
        <ol>{"".join(f"<li>{html.escape(item)}</li>" for item in postman["instructions"])}</ol>
    </div>
    """


def build_webhooks_body(app, *, result: dict | None = None, error: str | None = None) -> str:
    status = svc.integration_status(app)
    webhooks = status["webhooks"]["endpoints"]
    options = "".join(
        f'<option value="{row.get("id", "")}">{html.escape(row.get("name") or row.get("endpoint_code", "Webhook"))}</option>'
        for row in webhooks
    ) or '<option value="">Default sandbox webhook</option>'
    result_html = ""
    if error:
        result_html = f'<div class="error">{html.escape(error)}</div>'
    elif result:
        result_html = f'<div class="success">Webhook test delivered.</div><pre>{html.escape(json.dumps(result, indent=2, default=str))}</pre>'
    return f"""
    {page_header("Webhook Test Console", "Simulate outbound webhook delivery and inspect signatures.")}
    {result_html}
    <div class="card">
        <form method="post" class="form-grid">
            <label>Webhook</label>
            <select name="webhook_id">{options}</select>
            <label>Event Type</label>
            <input name="event_type" value="OrderCreated" />
            <label>Payload JSON</label>
            <textarea name="payload" rows="8">{{"order_id":"ORD-TEST-001","status":"CREATED"}}</textarea>
            <button class="btn" type="submit">Send Test Webhook</button>
        </form>
    </div>
    <div class="card">
        <h3>Integration Status</h3>
        <p>Platform: {html.escape(status["status"])} · Webhooks configured: {status["webhooks"]["count"]}</p>
    </div>
    """


def build_sandbox_body(app, *, result: dict | None = None, error: str | None = None) -> str:
    examples = svc.sandbox_payload_examples()
    result_html = ""
    if error:
        result_html = f'<div class="error">{html.escape(error)}</div>'
    elif result:
        result_html = f'<div class="success">Sandbox request completed.</div><pre>{html.escape(json.dumps(result, indent=2, default=str))}</pre>'
    api_example = json.dumps(examples["api_request"], indent=2)
    adapter_block = "".join(
        f"<h4>{adapter}</h4><pre>{html.escape(json.dumps(item, indent=2))}</pre>"
        for adapter, item in examples["adapters"].items()
    )
    return f"""
    {page_header("Integration Sandbox", "Run sample API and adapter payloads safely.")}
    {result_html}
    <div class="card">
        <h3>API Sandbox Console</h3>
        <form method="post" class="form-grid">
            <input type="hidden" name="mode" value="api" />
            <label>HTTP Method</label>
            <input name="method" value="GET" />
            <label>Path</label>
            <input name="path" value="/api/v1/api-platform/health" />
            <label>Headers JSON</label>
            <textarea name="headers" rows="3">{{}}</textarea>
            <label>Body JSON</label>
            <textarea name="body" rows="4"></textarea>
            <button class="btn" type="submit">Execute Sandbox Request</button>
        </form>
        <p>Equivalent API: <code>{examples["execute_endpoint"]}</code></p>
        <pre>{html.escape(api_example)}</pre>
    </div>
    <div class="card">
        <h3>Adapter Payload Examples</h3>
        {adapter_block}
    </div>
    """


def build_onboarding_body() -> str:
    checklist = svc.onboarding_checklist()
    items = []
    for step in checklist["steps"]:
        links = " · ".join(f'<a href="{href}">{href}</a>' for href in step.get("links", []))
        items.append(
            f"<li><strong>{step['id']}. {html.escape(step['title'])}</strong><br>"
            f"{html.escape(step['detail'])}<br>{links}</li>"
        )
    return f"""
    {page_header("Partner Onboarding Checklist", checklist["title"])}
    <div class="card">
        <ol class="checklist">{"".join(items)}</ol>
    </div>
    <div class="card">
        <h3>Verification Report</h3>
        <p>Run the verification script to produce <code>generated_release/DEVELOPER_PORTAL_REPORT.json</code>:</p>
        <pre>DATABASE_URL=sqlite:///tmp/dxcon_dev.db python backend/scripts/verify_developer_portal.py</pre>
    </div>
    """
