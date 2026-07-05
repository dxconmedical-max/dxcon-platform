"""Marketplace Platform web rendering helpers — Phase 7.2."""

from __future__ import annotations

import html
import json

from app.services import marketplace_platform_service as svc
from app.web.demo_pilot_lib import metric_cards, page_header, pilot_styles

MP_NAV = (
    ("Overview", "/marketplace-platform"),
    ("Marketplace", "/marketplace-platform/marketplace"),
    ("Plugin Registry", "/marketplace-platform/registry"),
    ("Plugin Manifest", "/marketplace-platform/manifest"),
    ("Plugin Installer", "/marketplace-platform/installer"),
    ("Plugin Version", "/marketplace-platform/versions"),
    ("Plugin Dependency", "/marketplace-platform/dependencies"),
    ("Plugin Permission", "/marketplace-platform/permissions"),
    ("Plugin Sandbox", "/marketplace-platform/sandbox"),
    ("Plugin Health", "/marketplace-platform/health"),
)


def mp_styles() -> str:
    return pilot_styles() + """
    pre { background:#0f172a; color:#e2e8f0; padding:12px; border-radius:8px; overflow:auto; white-space:pre-wrap; font-size:13px; }
    .muted-note { color:#64748b; font-size:13px; margin-bottom:16px; }
    .flow { background:#0f172a; color:#e2e8f0; padding:16px; border-radius:8px; font-family:monospace; line-height:1.6; text-align:center; margin-bottom:16px; font-size:13px; }
    """


def render_mp_page(title: str, body_html: str) -> str:
    nav = "".join(f'<a href="{href}">{label}</a>' for label, href in MP_NAV)
    return f"""
    <html>
    <head>
        <title>{title}</title>
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <style>{mp_styles()}</style>
    </head>
    <body>
        <div class="wrap">
            <div class="nav">{nav}</div>
            <div class="muted-note">Marketplace & plugin platform · Phase 7.2</div>
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
            ("Active Services", summary["active_services"]),
            ("Bookings", summary["bookings_total"]),
            ("Plugins Registered", summary["plugins_registered"]),
            ("Plugins Installed", summary["plugins_installed"]),
            ("Health Checks", summary["plugin_health_passed"]),
        ]
    )
    features = "".join(f"<li>{html.escape(item)}</li>" for item in data["features"])
    flow = """
    Marketplace → Plugin Registry → Manifest → Installer → Version → Dependency → Permission → Sandbox → Health
    """
    return f"""
    {page_header("Marketplace Platform", "Diagnostic marketplace and extensible plugin ecosystem.")}
    <div class="flow">{flow}</div>
    {cards}
    <div class="card"><h3>Phase 7.2 Features</h3><ul>{features}</ul></div>
    """


def build_marketplace_body() -> str:
    data = svc.marketplace_overview()
    return f"""
    {page_header("Marketplace", "Service catalog and booking overview.")}
    {metric_cards([
        ("Active Services", data.get("active_services", 0)),
        ("Active Partners", data.get("active_partners", 0)),
        ("Service Mappings", data.get("service_mappings", 0)),
        ("Bookings", data.get("bookings_total", 0)),
    ])}
    <div class="card"><p>Legacy marketplace: <a href="/marketplace">/marketplace</a></p></div>
    """


def build_registry_body() -> str:
    data = svc.plugin_registry()
    rows = [
        [
            html.escape(str(row.get("plugin_id", ""))),
            html.escape(str(row.get("name", ""))),
            str(row.get("version", "")),
            "Yes" if row.get("enabled") else "No",
        ]
        for row in data.get("plugins", [])[:20]
    ]
    return f"""
    {page_header("Plugin Registry", f"{data.get('registry_count', 0)} plugins registered.")}
    <div class="card">{_table(["ID", "Name", "Version", "Enabled"], rows)}</div>
    """


def build_manifest_body() -> str:
    data = svc.plugin_manifests()
    rows = [
        [
            html.escape(str(row.get("plugin_id", ""))),
            html.escape(str(row.get("name", ""))),
            str(row.get("version", "")),
            html.escape(str(row.get("description", ""))[:60]),
        ]
        for row in data.get("manifests", [])[:20]
    ]
    return f"""
    {page_header("Plugin Manifest", f"{data.get('count', 0)} manifests.")}
    <div class="card">{_table(["ID", "Name", "Version", "Description"], rows)}</div>
    """


def build_installer_body() -> str:
    data = svc.plugin_installer()
    rows = [
        [
            html.escape(str(row.get("plugin_id", ""))),
            str(row.get("version", "")),
            "Yes" if row.get("installed") else "No",
            "Yes" if row.get("enabled") else "No",
        ]
        for row in data.get("installs", [])[:20]
    ]
    return f"""
    {page_header("Plugin Installer", f"{data.get('count', 0)} install records.")}
    <div class="card">{_table(["ID", "Version", "Installed", "Enabled"], rows)}</div>
    """


def build_versions_body() -> str:
    data = svc.plugin_versions()
    rows = [
        [html.escape(str(row.get("plugin_id", ""))), str(row.get("version", "")), str(row.get("status", ""))]
        for row in data.get("versions", [])[:20]
    ]
    return f"""
    {page_header("Plugin Version", f"{data.get('count', 0)} version records.")}
    <div class="card">{_table(["ID", "Version", "Status"], rows)}</div>
    """


def build_dependencies_body() -> str:
    data = svc.plugin_dependencies()
    rows = [
        [
            html.escape(str(row.get("plugin_id", ""))),
            str(row.get("dependency_count", 0)),
            ", ".join(row.get("dependencies", [])) or "—",
        ]
        for row in data.get("dependencies", [])[:20]
    ]
    return f"""
    {page_header("Plugin Dependency", f"{data.get('count', 0)} dependency graphs.")}
    <div class="card">{_table(["ID", "Count", "Dependencies"], rows)}</div>
    """


def build_permissions_body() -> str:
    data = svc.plugin_permissions()
    rows = [
        [
            html.escape(str(row.get("plugin_id", ""))),
            str(row.get("permission_count", 0)),
            ", ".join(row.get("permissions", [])),
        ]
        for row in data.get("permissions", [])[:20]
    ]
    return f"""
    {page_header("Plugin Permission", f"{data.get('count', 0)} permission maps.")}
    <div class="card">{_table(["ID", "Count", "Permissions"], rows)}</div>
    """


def build_sandbox_body() -> str:
    data = svc.plugin_sandbox()
    return build_json_section("Plugin Sandbox", data)


def build_health_body() -> str:
    data = svc.plugin_health()
    rows = [
        [
            html.escape(str(row.get("plugin_id", ""))),
            str(row.get("health", {}).get("status", "")),
            "Yes" if row.get("ok") else "No",
        ]
        for row in data.get("checks", [])[:20]
    ]
    return f"""
    {page_header("Plugin Health", f"{data.get('checks_passed', 0)}/{data.get('checks_total', 0)} checks passed.")}
    <div class="card">{_table(["ID", "Status", "OK"], rows)}</div>
    """


def build_json_section(title: str, data: dict) -> str:
    return f"""
    {page_header(title, data.get("report", ""))}
    <div class="card"><pre>{html.escape(json.dumps(data, indent=2, default=str))}</pre></div>
    """
