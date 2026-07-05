"""Pilot Toolkit web rendering helpers — Phase 5 Sprint 5.13."""

from __future__ import annotations

import html

from app.services import pilot_toolkit_service as svc
from app.web.demo_pilot_lib import metric_cards, page_header, pilot_styles

TOOLKIT_NAV = (
    ("Overview", "/pilot-toolkit"),
    ("Demo Accounts", "/pilot-toolkit/demo-accounts"),
    ("Demo Data", "/pilot-toolkit/demo-data"),
    ("Postman", "/pilot-toolkit/postman"),
    ("Swagger", "/pilot-toolkit/swagger"),
    ("Workflow", "/pilot-toolkit/workflow"),
    ("PDF", "/pilot-toolkit/pdf"),
    ("QR", "/pilot-toolkit/qr"),
    ("Reports", "/pilot-toolkit/reports"),
)


def toolkit_styles() -> str:
    return pilot_styles() + """
    .flow { background:#0f172a; color:#e2e8f0; padding:16px; border-radius:8px; font-family:monospace; line-height:1.6; text-align:center; margin-bottom:16px; font-size:13px; }
    .muted-note { color:#64748b; font-size:13px; margin-bottom:16px; }
    .links a { margin-right:12px; }
    pre { background:#0f172a; color:#e2e8f0; padding:12px; border-radius:8px; overflow:auto; white-space:pre-wrap; }
    """


def render_toolkit_page(title: str, body_html: str) -> str:
    nav = "".join(f'<a href="{href}">{label}</a>' for label, href in TOOLKIT_NAV)
    return f"""
    <html>
    <head>
        <title>{title}</title>
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <style>{toolkit_styles()}</style>
    </head>
    <body>
        <div class="wrap">
            <div class="nav">{nav}</div>
            <div class="muted-note">Pilot demo resources · Phase 5 Sprint 5.13</div>
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
            ("Demo Accounts", summary["demo_accounts_total"]),
            ("Demo Orders", summary["demo_orders"]),
            ("Workflow Steps", summary["workflow_steps"]),
            ("PDF Samples", summary["pdf_samples"]),
            ("QR Boxes", summary["qr_boxes"]),
            ("Postman", "OK" if summary["postman_available"] else "—"),
            ("Swagger", "OK" if summary["swagger_available"] else "—"),
        ]
    )
    features = "".join(f"<li>{item}</li>" for item in data["features"])
    flow = """
    Demo Accounts → Demo Data → Postman → Swagger → Workflow → PDF → QR → Reports
    """
    return f"""
    {page_header("Pilot Toolkit", "Demo accounts, API docs, workflow walkthrough, and report assets.")}
    <div class="flow">{flow}</div>
    {cards}
    <div class="card" style="margin-top:20px;">
        <h3>Sprint 5.13 Features</h3>
        <ul>{features}</ul>
    </div>
    """


def build_demo_accounts_body() -> str:
    data = svc.demo_accounts()
    rows = []
    for role, accounts in data["accounts_by_role"].items():
        for account in accounts[:5]:
            rows.append(
                [
                    html.escape(role.upper()),
                    html.escape(account.get("email", "")),
                    html.escape(account.get("role", "")),
                    html.escape(account.get("password", "")[:40]),
                ]
            )
    return f"""
    {page_header("Demo Accounts", f"Password: {data['demo_password']}")}
    {metric_cards([("Accounts", data["accounts_total"])])}
    <div class="card links"><a href="/demo-accounts">Full Demo Accounts Page</a> · <a href="/login">Login</a></div>
    <div class="card"><h3>Sample Accounts</h3>{_table(["Role Group", "Email", "Role", "Password"], rows)}</div>
    """


def build_demo_data_body() -> str:
    data = svc.demo_data()
    summary = data["seeded_summary"]
    return f"""
    {page_header("Demo Data", "Seeded pilot dataset summary.")}
    {metric_cards([
        ("Users", summary["users"]),
        ("Patients", summary["patients"]),
        ("Orders", summary["orders"]),
        ("Tests", summary["test_catalog"]),
    ])}
    <div class="card"><h3>Seed API</h3><pre>{html.escape(data["seed_api"])}</pre></div>
    <div class="card"><h3>System</h3><p>Status: {html.escape(data["system_status"]["status"])} · DB: {html.escape(data["system_status"]["database"])}</p></div>
    """


def build_postman_body() -> str:
    data = svc.postman_toolkit()
    steps = "".join(f"<li>{html.escape(step)}</li>" for step in data.get("instructions", []))
    return f"""
    {page_header("Postman", "Import collection for API exploration.")}
    {metric_cards([
        ("Available", "Yes" if data["collection_available"] else "No"),
        ("Items", data["collection_items"]),
    ])}
    <div class="card links">
        <a href="{html.escape(data['collection_url'])}">Download Collection</a>
        <a href="{html.escape(data['openapi_import'])}">OpenAPI Import</a>
        <a href="/developer-portal/postman">Developer Portal</a>
    </div>
    <div class="card"><h3>Instructions</h3><ol>{steps}</ol></div>
    """


def build_swagger_body() -> str:
    data = svc.swagger_toolkit()
    links = "".join(
        f'<a href="{html.escape(url)}">{html.escape(label)}</a> '
        for label, url in (
            ("Swagger UI", data["swagger_ui"]),
            ("ReDoc", data["redoc"]),
            ("OpenAPI JSON", data["openapi_json"]),
            ("OpenAPI YAML", data["openapi_yaml"]),
            ("Docs Index", data["docs_index"]),
        )
    )
    return f"""
    {page_header("Swagger", "Interactive API documentation.")}
    {metric_cards([
        ("OpenAPI JSON", "OK" if data["files"]["openapi_json"] else "Missing"),
        ("OpenAPI YAML", "OK" if data["files"]["openapi_yaml"] else "Missing"),
    ])}
    <div class="card links">{links}</div>
    """


def build_workflow_body() -> str:
    data = svc.workflow_toolkit()
    rows = [
        [str(step["step"]), html.escape(step["label"]), html.escape(step["route"]), html.escape(step["detail"])]
        for step in data.get("steps", [])
    ]
    return f"""
    {page_header("Workflow", data.get("timeline", ""))}
    {metric_cards([("Steps", data["steps_total"])])}
    <div class="card links"><a href="/workflow-demo">Interactive Workflow Demo</a></div>
    <div class="card"><h3>Timeline</h3>{_table(["#", "Stage", "Route", "Detail"], rows)}</div>
    """


def build_pdf_body() -> str:
    data = svc.pdf_toolkit()
    rows = [
        [
            html.escape(row["order_code"]),
            "Yes" if row["has_results"] else "No",
            f'<a href="{html.escape(row["pdf_route"])}">PDF</a>',
        ]
        for row in data.get("demo_orders", [])[:15]
    ]
    return f"""
    {page_header("PDF", data["pdf_route_pattern"])}
    {metric_cards([
        ("Demo Orders", data["demo_orders_total"]),
        ("With Results", data["orders_with_results"]),
    ])}
    <div class="card"><h3>Sample PDF Reports</h3>{_table(["Order", "Has Results", "Link"], rows)}</div>
    """


def build_qr_body() -> str:
    data = svc.qr_toolkit()
    rows = [
        [
            html.escape(row["box_code"]),
            f'<a href="{html.escape(row["qr_route"])}">QR</a>',
            html.escape(str(row.get("status") or "—")),
        ]
        for row in data.get("transport_boxes", [])[:15]
    ]
    related = "".join(f'<a href="{html.escape(route)}">{html.escape(route)}</a> ' for route in data.get("related_routes", []))
    return f"""
    {page_header("QR", data["qr_route_pattern"])}
    {metric_cards([("Boxes", data["boxes_total"])])}
    <div class="card links">{related}</div>
    <div class="card"><h3>Transport Box QR</h3>{_table(["Box Code", "Link", "Status"], rows)}</div>
    """


def build_reports_body() -> str:
    data = svc.reports_toolkit()
    kpi = data.get("kpi_summary", {})
    revenue = data.get("revenue_summary", {})
    web_links = "".join(f'<a href="{html.escape(route)}">{html.escape(route)}</a> ' for route in data.get("web_routes", []))
    api_links = "".join(f'<li>{html.escape(route)}</li>' for route in data.get("api_routes", []))
    return f"""
    {page_header("Reports", "BI dashboards and reporting APIs.")}
    {metric_cards([
        ("Orders", kpi.get("orders_total", 0)),
        ("Bookings", kpi.get("daily_bookings", 0)),
        ("Revenue", revenue.get("gross_revenue", 0)),
        ("Samples", kpi.get("samples_total", 0)),
    ])}
    <div class="card links">{web_links}</div>
    <div class="card"><h3>API Routes</h3><ul>{api_links}</ul></div>
    """
