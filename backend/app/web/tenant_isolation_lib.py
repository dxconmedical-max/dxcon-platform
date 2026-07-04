"""Tenant Isolation web rendering helpers — Phase 5 Sprint 5.4."""

from __future__ import annotations

import html

from app.services import tenant_isolation_service as svc
from app.web.demo_pilot_lib import metric_cards, page_header, pilot_styles

TENANT_NAV = (
    ("One Platform", "/tenant-isolation"),
    ("Clinic A", "/tenant-isolation/clinic-a"),
    ("Clinic B", "/tenant-isolation/clinic-b"),
    ("Clinic C", "/tenant-isolation/clinic-c"),
    ("Isolation", "/tenant-isolation/isolation"),
)


def tenant_styles() -> str:
    return pilot_styles() + """
    .feature-list { font-size:13px; color:#334155; line-height:1.6; }
    .flow { background:#0f172a; color:#e2e8f0; padding:16px; border-radius:8px; font-family:monospace; line-height:1.8; text-align:center; margin-bottom:16px; }
    .checklist li { margin-bottom:10px; }
    pre { background:#0f172a; color:#e2e8f0; padding:12px; border-radius:8px; overflow:auto; white-space:pre-wrap; }
    """


def render_tenant_page(title: str, body_html: str) -> str:
    nav = "".join(f'<a href="{href}">{label}</a>' for label, href in TENANT_NAV)
    return f"""
    <html>
    <head>
        <title>{title}</title>
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <style>{tenant_styles()}</style>
    </head>
    <body>
        <div class="wrap">
            <div class="nav">{nav}</div>
            <div class="muted">Multi-tenant clinic isolation · Phase 5 Sprint 5.4</div>
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


def _architecture_flow() -> str:
    return """
    <div class="flow">
        Clinic A<br>Clinic B<br>Clinic C<br>
        ↓<br>
        One Platform<br>
        ↓<br>
        Tenant Isolation
    </div>
    """


def build_platform_body() -> str:
    data = svc.dashboard_payload()
    platform = svc.one_platform()
    summary = data["summary"]
    cards = metric_cards(
        [
            ("Demo Clinics", summary["demo_clinics"]),
            ("Tenants", summary["tenants_total"]),
            ("Strict Isolation", summary["strict_isolation_count"]),
            ("Isolation Checks", f"{summary['isolation_checks_passed']}/{summary['isolation_checks_total']}"),
        ]
    )
    rows = [
        [
            html.escape(item.get("label", "")),
            html.escape(str(item.get("tenant", {}).get("tenant_code", ""))),
            html.escape(str(item.get("tenant", {}).get("isolation_mode", ""))),
            html.escape(str(item.get("isolation", {}).get("schema_name", ""))),
        ]
        for item in platform.get("demo_clinics", [])
    ]
    features = "".join(f"<li>{item}</li>" for item in data["features"])
    return f"""
    {page_header("One Platform", "Clinic A, B, and C on a single DxCon platform with strict tenant isolation.")}
    {_architecture_flow()}
    <div class="card"><strong>Status:</strong> {html.escape(data['status'])}</div>
    {cards}
    <div class="card"><h3>Demo Clinic Tenants</h3>{_table(["Clinic", "Tenant Code", "Isolation", "Schema"], rows)}</div>
    <div class="card"><h3>Features</h3><ul class="feature-list">{features}</ul></div>
    """


def build_clinic_body(key: str) -> str:
    loaders = {
        "clinic-a": svc.clinic_a,
        "clinic-b": svc.clinic_b,
        "clinic-c": svc.clinic_c,
    }
    data = loaders[key]()
    tenant = data["tenant"]
    isolation = data["isolation"]
    org_rows = [
        [
            html.escape(str(item.get("org_code", ""))),
            html.escape(str(item.get("name", ""))),
            html.escape(str(item.get("level", ""))),
        ]
        for item in data.get("organizations", [])
    ]
    return f"""
    {page_header(data['label'], "Dedicated tenant namespace on the shared DxCon platform.")}
    <div class="card">
        <p><strong>Tenant:</strong> {html.escape(tenant.get('name', ''))}</p>
        <p><strong>Code:</strong> {html.escape(tenant.get('tenant_code', ''))}</p>
        <p><strong>Isolation:</strong> {html.escape(tenant.get('isolation_mode', ''))}</p>
        <p><strong>Schema:</strong> {html.escape(tenant.get('schema_name', ''))}</p>
        <p><strong>Header:</strong> {html.escape(data.get('platform_header', ''))}</p>
        <p><strong>Isolated:</strong> {isolation.get('isolated')}</p>
    </div>
    <div class="card"><h3>Organizations</h3>{_table(["Code", "Name", "Level"], org_rows)}</div>
    """


def build_isolation_body() -> str:
    data = svc.tenant_isolation_matrix()
    rows = [
        [
            html.escape(str(item.get("tenant_code", ""))),
            html.escape(str(item.get("name", ""))),
            html.escape(str(item.get("isolation_mode", ""))),
            html.escape(str(item.get("schema_name", ""))),
            "Yes" if item.get("isolated") else "No",
        ]
        for item in data.get("matrix", [])
    ]
    checks = "".join(
        f"<li><strong>{html.escape(item['title'])}</strong> — {html.escape(item['detail'])} "
        f"[{html.escape(item['status'])}]</li>"
        for item in data.get("checks", [])
    )
    return f"""
    {page_header("Tenant Isolation", "Boundary checks across all clinic tenants on the platform.")}
    <div class="card"><p>Checks passed: {data.get('checks_passed', 0)}/{data.get('checks_total', 0)}</p></div>
    <div class="card"><h3>Isolation Matrix</h3>{_table(["Code", "Name", "Mode", "Schema", "Isolated"], rows)}</div>
    <div class="card"><h3>Verification Checklist</h3><ul class="checklist">{checks}</ul></div>
    <div class="card"><h3>Legacy API</h3><pre>{html.escape(data.get('legacy_api', ''))}</pre></div>
    """
