"""Multi Tenant Foundation web rendering helpers — Phase 7.1."""

from __future__ import annotations

import html
import json

from app.services import multi_tenant_foundation_service as svc
from app.web.demo_pilot_lib import metric_cards, page_header, pilot_styles

MTF_NAV = (
    ("Overview", "/multi-tenant"),
    ("Tenants", "/multi-tenant/tenants"),
    ("Organizations", "/multi-tenant/organizations"),
    ("Clinics", "/multi-tenant/clinics"),
    ("Laboratories", "/multi-tenant/laboratories"),
    ("Settings", "/multi-tenant/settings"),
    ("Resolver", "/multi-tenant/resolver"),
    ("Context", "/multi-tenant/context"),
    ("Middleware", "/multi-tenant/middleware"),
    ("Admin", "/multi-tenant/admin"),
    ("Audit", "/multi-tenant/audit"),
    ("Isolation", "/multi-tenant/isolation"),
)


def mtf_styles() -> str:
    return pilot_styles() + """
    pre { background:#0f172a; color:#e2e8f0; padding:12px; border-radius:8px; overflow:auto; white-space:pre-wrap; font-size:13px; }
    .muted-note { color:#64748b; font-size:13px; margin-bottom:16px; }
    .flow { background:#0f172a; color:#e2e8f0; padding:16px; border-radius:8px; font-family:monospace; line-height:1.6; text-align:center; margin-bottom:16px; font-size:13px; }
    """


def render_mtf_page(title: str, body_html: str) -> str:
    nav = "".join(f'<a href="{href}">{label}</a>' for label, href in MTF_NAV)
    return f"""
    <html>
    <head>
        <title>{title}</title>
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <style>{mtf_styles()}</style>
    </head>
    <body>
        <div class="wrap">
            <div class="nav">{nav}</div>
            <div class="muted-note">Enterprise multi-tenant foundation · Phase 7.1</div>
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
            ("Tenants", summary["tenants_total"]),
            ("Organizations", summary["organizations_total"]),
            ("Clinics", summary["clinics_total"]),
            ("Laboratories", summary["laboratories_total"]),
            ("Org Settings", summary["settings_total"]),
            ("Isolation Checks", summary["isolation_checks_passed"]),
        ]
    )
    features = "".join(f"<li>{html.escape(item)}</li>" for item in data["features"])
    flow = """
    Tenant → Organization → Clinic / Laboratory → Settings → Resolver → Context → Middleware → Admin → Audit → Isolation
    """
    return f"""
    {page_header("Multi Tenant Foundation", "Enterprise tenant, organization, and isolation framework.")}
    <div class="flow">{flow}</div>
    {cards}
    <div class="card"><h3>Phase 7.1 Features</h3><ul>{features}</ul></div>
    """


def build_tenants_body() -> str:
    data = svc.tenant_registry()
    rows = [
        [html.escape(str(row.get("tenant_code", ""))), html.escape(str(row.get("name", ""))), str(row.get("status", ""))]
        for row in data.get("tenants", [])[:20]
    ]
    return f"""
    {page_header("Tenants", f"{data.get('count', 0)} enterprise tenants registered.")}
    <div class="card">{_table(["Code", "Name", "Status"], rows)}</div>
    """


def build_organizations_body() -> str:
    data = svc.organization_registry()
    rows = [
        [html.escape(str(row.get("org_code", ""))), html.escape(str(row.get("name", ""))), str(row.get("tenant_id", ""))]
        for row in data.get("organizations", [])[:20]
    ]
    return f"""
    {page_header("Organizations", f"{data.get('count', 0)} organizations across tenants.")}
    <div class="card">{_table(["Code", "Name", "Tenant"], rows)}</div>
    """


def build_clinics_body() -> str:
    data = svc.clinic_registry()
    rows = [
        [
            html.escape(str(row.get("clinic_code", ""))),
            html.escape(str(row.get("name", ""))),
            str(row.get("tenant_id") or "—"),
        ]
        for row in data.get("clinics", [])[:20]
    ]
    return f"""
    {page_header("Clinics", f"{data.get('count', 0)} clinic profiles.")}
    <div class="card">{_table(["Code", "Name", "Tenant"], rows)}</div>
    """


def build_laboratories_body() -> str:
    data = svc.laboratory_registry()
    rows = [
        [
            html.escape(str(row.get("code", ""))),
            html.escape(str(row.get("name", ""))),
            str(row.get("tenant_id") or "—"),
        ]
        for row in data.get("laboratories", [])[:20]
    ]
    return f"""
    {page_header("Laboratories", f"{data.get('count', 0)} laboratory entities.")}
    <div class="card">{_table(["Code", "Name", "Tenant"], rows)}</div>
    """


def build_settings_body() -> str:
    data = svc.organization_settings()
    rows = [
        [
            html.escape(str(row.get("setting_key", ""))),
            html.escape(str(row.get("category", ""))),
            str(row.get("tenant_id") or "—"),
        ]
        for row in data.get("settings", [])[:20]
    ]
    return f"""
    {page_header("Organization Settings", f"{data.get('count', 0)} tenant/org settings.")}
    <div class="card">{_table(["Key", "Category", "Tenant"], rows)}</div>
    """


def build_json_section(title: str, data: dict) -> str:
    return f"""
    {page_header(title, data.get("report", ""))}
    <div class="card"><pre>{html.escape(json.dumps(data, indent=2, default=str))}</pre></div>
    """


def build_resolver_body() -> str:
    return build_json_section("Tenant Resolver", svc.tenant_resolver_status())


def build_context_body() -> str:
    return build_json_section("Tenant Context", svc.tenant_context_status())


def build_middleware_body() -> str:
    return build_json_section("Tenant Middleware", svc.tenant_middleware_status())


def build_admin_body() -> str:
    return build_json_section("Tenant Admin", svc.tenant_admin_overview())


def build_audit_body() -> str:
    data = svc.tenant_audit_log()
    rows = [
        [
            html.escape(str(row.get("action", ""))),
            html.escape(str(row.get("actor_email") or "—")),
            str(row.get("tenant_id") or "—"),
        ]
        for row in data.get("records", [])[:20]
    ]
    return f"""
    {page_header("Tenant Audit", f"{data.get('count', 0)} audit records.")}
    <div class="card">{_table(["Action", "Actor", "Tenant"], rows)}</div>
    """


def build_isolation_body() -> str:
    return build_json_section("Tenant Isolation Framework", svc.tenant_isolation_framework())
