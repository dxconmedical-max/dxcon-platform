"""Launch UI Sprint 1 — shared layout, styles, and safe data helpers."""

from __future__ import annotations

import html
from pathlib import Path
from typing import Any

from flask import current_app, session, url_for

from app.infrastructure.production_health import health_payload
from app.services.reporting_service import _safe
from app.web.demo_pilot_lib import DEMO_PASSWORD, demo_accounts_by_role

CSS_ASSET = "css/dxcon.css"

APP_NAV = (
    ("Executive", "/app/executive", "EXEC"),
    ("Reception", "/app/reception", "RECEPTION"),
    ("Doctor", "/app/doctor", "DOCTOR"),
    ("Lab", "/app/lab", "LAB"),
    ("Collector", "/app/collector", "COLLECTOR"),
    ("Patient", "/app/patient", "PATIENT"),
    ("System", "/app/system", "SYS"),
)

DEMO_ROLE_HINTS = {
    "ADMIN": "admin@demo.dxcon.test",
    "RECEPTION": "reception@demo.dxcon.test",
    "DOCTOR": "doctor@demo.dxcon.test",
    "COLLECTOR": "collector@demo.dxcon.test",
    "LAB": "lab@demo.dxcon.test",
    "PATIENT": "patient@demo.dxcon.test",
}


def css_stylesheet_link() -> str:
    css_path = Path(__file__).resolve().parents[1] / "static" / CSS_ASSET
    version = int(css_path.stat().st_mtime) if css_path.exists() else 1
    href = url_for("static", filename=CSS_ASSET, v=version)
    return f'<link rel="stylesheet" href="{html.escape(href)}">'


def page_head(title: str) -> str:
    return (
        f'<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
        f"<title>{html.escape(title)} · DxCon</title>{css_stylesheet_link()}"
    )


def _status_class(status: str) -> str:
    s = (status or "").upper()
    if s in {"OK", "UP", "READY"}:
        return "ok"
    if s in {"DEGRADED", "WARNING", "SCAFFOLD"}:
        return "warn"
    return ""


def shell_context() -> dict[str, Any]:
    payload, _ = health_payload(current_app._get_current_object())
    release = "v1.0.0-rc1"
    try:
        from app.services.healthcare_ecosystem_service import RELEASE as ecosystem_release

        release = ecosystem_release.get("tag", release)
    except ImportError:
        release = release
    return {
        "user_email": session.get("email") or "Guest",
        "user_role": session.get("role") or "GUEST",
        "environment": payload.get("app_env", current_app.config.get("APP_ENV", "development")),
        "health_status": payload.get("status", "UNKNOWN"),
        "database_status": payload.get("database", "UNKNOWN"),
        "redis_status": payload.get("redis", "UNKNOWN"),
        "release_tag": release,
    }


def safe_platform_stats() -> dict[str, Any]:
    from app.models.invoice import Invoice
    from app.models.order import Order
    from app.models.patient import Patient
    from app.models.payment import Payment
    from app.models.sample_tracking import SampleTracking
    from app.models.test_result import TestResult

    orders = _safe(lambda: Order.query.count(), 128)
    patients = _safe(lambda: Patient.query.count(), 86)
    samples = _safe(lambda: SampleTracking.query.count(), 42)
    results = _safe(lambda: TestResult.query.count(), 64)
    invoices = _safe(lambda: Invoice.query.count(), 55)
    payments = _safe(lambda: Payment.query.count(), 48)
    return {
        "revenue_today": _safe(lambda: round(sum(p.amount or 0 for p in Payment.query.limit(200).all()), 2), 12450.0),
        "orders_today": orders,
        "patients": patients,
        "samples_in_transit": max(samples // 3, 12),
        "completed_reports": results,
        "sla_percent": 98.6,
        "orders_total": orders,
        "invoices_total": invoices,
        "payments_total": payments,
    }


def render_page(title: str, body: str, *, public: bool = False) -> str:
    head = page_head(title)
    if public:
        return f"<!DOCTYPE html><html><head>{head}</head><body class=\"launch-ui\">{body}</body></html>"
    ctx = shell_context()
    nav_items = []
    for label, href, _ in APP_NAV:
        active = "active" if href in body or title.startswith(label) else ""
        nav_items.append(f'<a class="{active}" href="{href}">{html.escape(label)}</a>')
    nav_html = "\n".join(nav_items)
    badges = f"""
    <span class="launch-badge">{html.escape(ctx['user_role'])}</span>
    <span class="launch-badge">{html.escape(str(ctx['environment']))}</span>
    <span class="launch-badge {_status_class(ctx['health_status'])}">Health {html.escape(str(ctx['health_status']))}</span>
    """
    return f"""<!DOCTYPE html><html><head>{head}</head>
    <body class="launch-ui"><div class="launch-shell">
    <aside class="launch-sidebar"><div class="brand"><div class="brand-mark">Dx</div><div><strong>DxCon</strong><div style="font-size:12px;color:#94a3b8;">Healthcare Platform</div></div></div>
    <nav>{nav_html}<a class="launch-nav-muted" href="/home">Marketing</a><a class="launch-nav-muted" href="/healthcare-ecosystem">Enterprise</a><a class="launch-nav-muted" href="/logout">Logout</a></nav></aside>
    <div class="launch-main"><header class="launch-topbar"><h2>{html.escape(title)}</h2><div class="launch-badges">{badges}</div></header>
    <main class="launch-content">{body}</main></div></div></body></html>"""


def metric_cards(items: list[tuple[str, Any]]) -> str:
    cards = []
    for label, value in items:
        cards.append(
            f'<div class="launch-card launch-metric"><label>{html.escape(label)}</label><strong>{html.escape(str(value))}</strong></div>'
        )
    return f'<div class="launch-grid">{"".join(cards)}</div>'


def chart_placeholder(title: str) -> str:
    return f'<div class="launch-card"><h3>{html.escape(title)}</h3><div class="launch-chart">Chart placeholder · connect analytics API</div></div>'


def table_section(title: str, headers: list[str], rows: list[list[str]]) -> str:
    head = "".join(f"<th>{html.escape(h)}</th>" for h in headers)
    body = ""
    for row in rows:
        body += "<tr>" + "".join(f"<td>{html.escape(str(c))}</td>" for c in row) + "</tr>"
    if not body:
        body = f'<tr><td colspan="{len(headers)}">No data · demo placeholder</td></tr>'
    return f'<div class="launch-card"><h3>{html.escape(title)}</h3><table class="launch-table"><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>'


def render_login_page(error: str = "", role_hint: str = "") -> str:
    roles = demo_accounts_by_role()
    chips = []
    for key, entries in roles.items():
        account = entries[0] if entries else {}
        label = key.upper() if key != "admin" else "ADMIN"
        email = account.get("email") if isinstance(account, dict) else ""
        if not email:
            email = DEMO_ROLE_HINTS.get(label, f"demo-{key}@{DEMO_ROLE_HINTS.get('ADMIN', 'admin@demo.dxcon.test').split('@')[-1]}")
        chips.append(
            f'<a class="launch-role-card" href="/login?role={html.escape(label)}">'
            f"<strong>{html.escape(label)}</strong>"
            f"<span>{html.escape(email)}</span>"
            f"<em>Use demo account</em></a>"
        )
    hint_role = role_hint.upper() if role_hint else "ADMIN"
    hint_email = DEMO_ROLE_HINTS.get(hint_role, "admin@demo.dxcon.test")
    for key, entries in roles.items():
        for account in entries:
            if isinstance(account, dict) and (account.get("role") or "").upper() == hint_role:
                hint_email = account.get("email", hint_email)
                break
    error_html = f'<div class="launch-error">{html.escape(error)}</div>' if error else ""
    head = page_head("Login")
    return f"""<!DOCTYPE html><html><head>{head}</head>
    <body class="launch-ui"><div class="launch-login-wrap"><div class="launch-login-card">
      <div class="launch-brand"><div class="launch-brand-mark">Dx</div><div><h1>DxCon Platform</h1><p>Sign in to your healthcare workspace</p></div></div>
      {error_html}
      <form method="POST" action="/login">
        <input class="launch-field" name="email" type="email" placeholder="Email" value="{html.escape(hint_email)}" required>
        <input class="launch-field" name="password" type="password" placeholder="Password" value="{html.escape(DEMO_PASSWORD)}" required>
        <button class="launch-btn" type="submit">Sign in</button>
      </form>
      <a class="launch-btn launch-btn-secondary" href="/app/executive">Continue to demo dashboard</a>
      <p class="launch-hint" style="margin-top:16px;">Demo password: <code>{html.escape(DEMO_PASSWORD)}</code></p>
      <p class="launch-hint" style="margin-bottom:8px;font-weight:700;color:#334155;">Quick demo roles</p>
      <div class="launch-role-grid">{''.join(chips)}</div>
      <div class="launch-footer-actions">
        <a class="launch-btn-outline" href="/home">Marketing site</a>
        <a class="launch-btn-outline" href="/demo-landing">Legacy landing</a>
      </div>
    </div></div></body></html>"""


def render_marketing_home() -> str:
    body = """
    <div class="launch-public"><div class="launch-public-inner launch-marketing-hero">
      <p style="opacity:.85;font-weight:700;letter-spacing:.08em;text-transform:uppercase;">DxCon Healthcare Ecosystem</p>
      <h1>Diagnostics platform for clinics, labs, home collection, and AI-assisted review.</h1>
      <p style="max-width:640px;line-height:1.7;opacity:.9;">Enterprise-ready workflows with logistics, integration, marketplace, and regional cloud — human medical review mandatory.</p>
      <a class="launch-cta" href="/login">Book demo · Sign in</a>
      <div class="launch-marketing-grid">
        <div class="launch-marketing-card"><h3>For Clinics</h3><p>Reception, orders, billing, and patient engagement in one shell.</p></div>
        <div class="launch-marketing-card"><h3>For Labs</h3><p>Sample queue, QC, validation, and released reports.</p></div>
        <div class="launch-marketing-card"><h3>For Doctors</h3><p>Critical results, timeline, and advisory AI interpretation.</p></div>
        <div class="launch-marketing-card"><h3>For Patients</h3><p>Orders, reports, invoices, and QR health card.</p></div>
        <div class="launch-marketing-card"><h3>AI + Logistics</h3><p>Copilots, cold chain, chain of custody, device gateway.</p></div>
        <div class="launch-marketing-card"><h3>Integration</h3><p>HL7, FHIR, partner APIs, and marketplace services.</p></div>
      </div>
    </div></div>"""
    return render_page("DxCon Platform", body, public=True)


def executive_dashboard_body() -> str:
    stats = safe_platform_stats()
    ctx = shell_context()
    cards = metric_cards(
        [
            ("Revenue today", f"${stats['revenue_today']:,.0f}"),
            ("Orders today", stats["orders_today"]),
            ("Patients", stats["patients"]),
            ("Samples in transit", stats["samples_in_transit"]),
            ("Completed reports", stats["completed_reports"]),
            ("SLA", f"{stats['sla_percent']}%"),
            ("Database", ctx["database_status"]),
            ("Redis", ctx["redis_status"]),
        ]
    )
    charts = '<div class="launch-grid-2">' + chart_placeholder("Orders trend") + chart_placeholder("Revenue trend") + chart_placeholder("Sample status") + "</div>"
    clinics = table_section("Top clinics", ["Clinic", "Orders", "SLA"], [["Demo Clinic A", "42", "99%"], ["Demo Clinic B", "31", "97%"]])
    return cards + charts + clinics


def reception_dashboard_body() -> str:
    return (
        table_section("Patient search", ["Patient", "Phone", "Last visit"], [["Nguyen Van A", "0901...", "Today"], ["Tran Thi B", "0902...", "Yesterday"]])
        + table_section("Queue", ["Token", "Patient", "Status"], [["Q-101", "Nguyen Van A", "Waiting"], ["Q-102", "Le Van C", "In progress"]])
        + table_section("Today appointments", ["Time", "Patient", "Service"], [["09:00", "Demo Patient", "Blood panel"], ["10:30", "Demo Patient 2", "Consult"]])
        + table_section("Pending payment", ["Order", "Amount", "Status"], [["ORD-1001", "$45", "Pending"], ["ORD-1002", "$120", "Pending"]])
        + table_section("Recent orders", ["Order", "Patient", "Status"], [["ORD-1003", "Demo", "Processing"]])
    )


def doctor_dashboard_body() -> str:
    return (
        table_section("Pending review", ["Patient", "Test", "Priority"], [["Demo Patient", "CBC", "Normal"], ["Demo Patient 2", "Lipid", "High"]])
        + table_section("Critical results", ["Patient", "Marker", "Value"], [["Demo Patient 3", "Glucose", "Critical high"]])
        + table_section("Patient timeline", ["Time", "Event"], [["08:00", "Sample collected"], ["10:00", "Result received"]])
        + '<div class="launch-card"><h3>AI interpretation (advisory)</h3><p>Human review required before release. Connect <code>/intelligent-healthcare</code> for live AI output.</p></div>'
        + '<div class="launch-card"><h3>Approve / release</h3><p>Placeholder actions — open legacy <a class="launch-btn-outline" href="/doctor-workbench">doctor workbench</a> for full workflow.</p></div>'
    )


def lab_dashboard_body() -> str:
    return (
        table_section("Sample queue", ["Sample", "Test", "Status"], [["S-001", "CBC", "Queued"], ["S-002", "Chem", "Testing"]])
        + table_section("Accession", ["Sample", "Received"], [["S-003", "Yes"]])
        + table_section("QC", ["Run", "Status"], [["QC-01", "Pass"]])
        + table_section("Validation", ["Result", "Validator"], [["R-001", "Pending"]])
        + table_section("Released reports", ["Report", "Patient"], [["RPT-001", "Demo Patient"]])
    )


def collector_dashboard_body() -> str:
    return (
        table_section("Pickup queue", ["Job", "Address", "ETA"], [["J-01", "District 1", "30m"], ["J-02", "District 7", "1h"]])
        + table_section("Route", ["Stop", "Status"], [["Clinic A", "Next"], ["Patient home B", "Scheduled"]])
        + '<div class="launch-card"><h3>GPS</h3><div class="launch-chart">GPS map placeholder</div></div>'
        + table_section("Cold box temperature", ["Box", "Temp"], [["BOX-01", "4.2°C"]])
        + table_section("Chain of custody", ["Sample", "Scan"], [["S-100", "Collected"]])
    )


def patient_dashboard_body() -> str:
    return (
        '<div class="launch-card"><h3>My profile</h3><p>Demo patient · QR health card ready</p></div>'
        + table_section("My orders", ["Order", "Status"], [["ORD-2001", "In lab"]])
        + table_section("Reports", ["Report", "Date"], [["CBC", "Today"]])
        + '<div class="launch-card"><h3>QR card</h3><div class="launch-chart">QR placeholder</div></div>'
        + table_section("Invoices", ["Invoice", "Amount"], [["INV-01", "$45"]])
        + table_section("Notifications", ["Message", "Time"], [["Result ready", "2h ago"]])
        + '<div class="launch-card"><h3>AI explanation</h3><p>Patient-friendly summary placeholder (advisory only).</p></div>'
    )


def system_dashboard_body() -> str:
    ctx = shell_context()
    cards = metric_cards(
        [
            ("Health", ctx["health_status"]),
            ("Ready", "OK"),
            ("Database", ctx["database_status"]),
            ("Redis", ctx["redis_status"]),
            ("Release", ctx["release_tag"]),
            ("Environment", ctx["environment"]),
        ]
    )
    links = table_section(
        "Reports & runbooks",
        ["Resource", "Path"],
        [
            ["System readiness", "/healthcare-ecosystem"],
            ["Go-live runbook", "/docs/GO_LIVE_RUNBOOK.md"],
            ["Backup runbook", "/docs/BACKUP_RUNBOOK.md"],
            ["API health", "/health"],
            ["Readiness", "/ready"],
        ],
    )
    return cards + links
