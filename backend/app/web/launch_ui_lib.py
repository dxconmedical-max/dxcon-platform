"""Launch UI Sprint 1 — shared layout, styles, and safe data helpers."""

from __future__ import annotations

import html
import json
from typing import Any

from flask import current_app, session, url_for

from app.infrastructure.production_health import health_payload
from app.services.reporting_service import _safe
from app.web.demo_pilot_lib import DEMO_PASSWORD, demo_accounts_by_role

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


def launch_css() -> str:
    return """
    :root {
      --bg: #0b1220;
      --panel: #111827;
      --panel-2: #1f2937;
      --border: #334155;
      --text: #e2e8f0;
      --muted: #94a3b8;
      --brand: #0ea5e9;
      --brand-2: #14b8a6;
      --ok: #22c55e;
      --warn: #f59e0b;
      --bad: #ef4444;
      --sidebar: 260px;
    }
    * { box-sizing: border-box; }
    body.launch-ui { margin:0; font-family: Inter, ui-sans-serif, system-ui, sans-serif; background:#f1f5f9; color:#0f172a; }
    a { color: inherit; text-decoration: none; }
    .launch-public { min-height:100vh; background: linear-gradient(135deg,#0f172a 0%,#134e4a 100%); color:white; }
    .launch-public-inner { max-width:1100px; margin:0 auto; padding:32px 20px 64px; }
    .launch-login-wrap { min-height:100vh; display:grid; place-items:center; background:linear-gradient(135deg,#0f172a,#1e3a8a); padding:24px; }
    .launch-login-card { width:100%; max-width:440px; background:white; border-radius:20px; padding:32px; box-shadow:0 25px 50px rgba(0,0,0,.25); }
    .launch-brand { display:flex; align-items:center; gap:12px; margin-bottom:24px; }
    .launch-brand-mark { width:44px; height:44px; border-radius:12px; background:linear-gradient(135deg,var(--brand),var(--brand-2)); display:grid; place-items:center; color:white; font-weight:800; }
    .launch-brand h1 { margin:0; font-size:22px; }
    .launch-brand p { margin:2px 0 0; color:#64748b; font-size:13px; }
    .launch-field { width:100%; padding:12px 14px; border:1px solid #cbd5e1; border-radius:10px; margin-bottom:12px; font-size:15px; }
    .launch-btn { width:100%; padding:12px 16px; border:none; border-radius:10px; background:linear-gradient(135deg,#0284c7,#0d9488); color:white; font-weight:700; cursor:pointer; font-size:15px; }
    .launch-btn-secondary { background:#e2e8f0; color:#0f172a; margin-top:10px; display:inline-block; text-align:center; }
    .launch-error { color:#b91c1c; background:#fef2f2; border:1px solid #fecaca; padding:10px 12px; border-radius:10px; margin-bottom:12px; font-size:14px; }
    .launch-hint { font-size:13px; color:#64748b; line-height:1.6; }
    .launch-role-grid { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:8px; margin:16px 0; }
    .launch-role-chip { border:1px solid #e2e8f0; border-radius:10px; padding:10px; font-size:12px; background:#f8fafc; cursor:pointer; }
    .launch-role-chip strong { display:block; color:#0f172a; margin-bottom:4px; }
    .launch-shell { display:grid; grid-template-columns: var(--sidebar) 1fr; min-height:100vh; }
    .launch-sidebar { background:var(--bg); color:var(--text); padding:20px 16px; border-right:1px solid var(--border); }
    .launch-sidebar .brand { display:flex; gap:10px; align-items:center; margin-bottom:24px; }
    .launch-sidebar .brand-mark { width:36px; height:36px; border-radius:10px; background:linear-gradient(135deg,var(--brand),var(--brand-2)); display:grid; place-items:center; font-weight:800; }
    .launch-sidebar nav a { display:block; padding:10px 12px; border-radius:10px; color:var(--muted); margin-bottom:4px; font-size:14px; }
    .launch-sidebar nav a.active, .launch-sidebar nav a:hover { background:var(--panel-2); color:white; }
    .launch-main { display:flex; flex-direction:column; min-width:0; }
    .launch-topbar { background:white; border-bottom:1px solid #e2e8f0; padding:14px 20px; display:flex; flex-wrap:wrap; gap:10px; align-items:center; justify-content:space-between; }
    .launch-topbar h2 { margin:0; font-size:20px; }
    .launch-badges { display:flex; flex-wrap:wrap; gap:8px; }
    .launch-badge { font-size:12px; font-weight:700; padding:6px 10px; border-radius:999px; background:#eff6ff; color:#1d4ed8; }
    .launch-badge.ok { background:#ecfdf5; color:#047857; }
    .launch-badge.warn { background:#fffbeb; color:#b45309; }
    .launch-content { padding:20px; flex:1; }
    .launch-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(180px,1fr)); gap:14px; }
    .launch-grid-2 { display:grid; grid-template-columns:repeat(auto-fit,minmax(320px,1fr)); gap:16px; }
    .launch-card { background:white; border:1px solid #e2e8f0; border-radius:16px; padding:18px; box-shadow:0 4px 14px rgba(15,23,42,.04); margin-bottom:16px; }
    .launch-card h3 { margin:0 0 12px; font-size:16px; }
    .launch-metric label { display:block; font-size:11px; text-transform:uppercase; letter-spacing:.05em; color:#64748b; margin-bottom:6px; font-weight:700; }
    .launch-metric strong { font-size:28px; color:#0f172a; }
    .launch-chart { height:140px; border-radius:12px; background:linear-gradient(180deg,#eff6ff,#f8fafc); border:1px dashed #cbd5e1; display:grid; place-items:center; color:#64748b; font-size:13px; }
    .launch-table { width:100%; border-collapse:collapse; font-size:14px; }
    .launch-table th, .launch-table td { padding:10px 8px; border-bottom:1px solid #e2e8f0; text-align:left; }
    .launch-table th { color:#64748b; font-size:12px; text-transform:uppercase; }
    .launch-section-title { margin:0 0 14px; font-size:18px; }
    .launch-marketing-hero { padding:48px 0 32px; }
    .launch-marketing-hero h1 { font-size:42px; margin:0 0 12px; max-width:720px; line-height:1.1; }
    .launch-marketing-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(240px,1fr)); gap:16px; margin-top:28px; }
    .launch-marketing-card { background:rgba(255,255,255,.08); border:1px solid rgba(255,255,255,.12); border-radius:16px; padding:22px; }
    .launch-cta { display:inline-block; margin-top:24px; padding:14px 22px; border-radius:12px; background:white; color:#0f172a; font-weight:800; }
    @media (max-width: 900px) {
      .launch-shell { grid-template-columns: 1fr; }
      .launch-sidebar { position:sticky; top:0; z-index:10; }
    }
    """


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
    css = launch_css()
    if public:
        return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{html.escape(title)} · DxCon</title><style>{css}</style></head><body class="launch-ui">{body}</body></html>"""
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
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{html.escape(title)} · DxCon</title><style>{css}</style></head>
    <body class="launch-ui"><div class="launch-shell">
    <aside class="launch-sidebar"><div class="brand"><div class="brand-mark">Dx</div><div><strong>DxCon</strong><div style="font-size:12px;color:#94a3b8;">Healthcare Platform</div></div></div>
    <nav>{nav_html}<a href="/home">Marketing</a><a href="/healthcare-ecosystem">Enterprise</a><a href="/logout">Logout</a></nav></aside>
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
            f'<a class="launch-role-chip" href="/login?role={html.escape(label)}"><strong>{html.escape(label)}</strong>{html.escape(email)}</a>'
        )
    hint_role = role_hint.upper() if role_hint else "ADMIN"
    hint_email = DEMO_ROLE_HINTS.get(hint_role, "admin@demo.dxcon.test")
    for key, entries in roles.items():
        for account in entries:
            if isinstance(account, dict) and (account.get("role") or "").upper() == hint_role:
                hint_email = account.get("email", hint_email)
                break
    error_html = f'<div class="launch-error">{html.escape(error)}</div>' if error else ""
    css = launch_css()
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Login · DxCon</title><style>{css}</style></head>
    <body class="launch-ui"><div class="launch-login-wrap"><div class="launch-login-card">
      <div class="launch-brand"><div class="launch-brand-mark">Dx</div><div><h1>DxCon Platform</h1><p>Sign in to your workspace</p></div></div>
      {error_html}
      <form method="POST" action="/login">
        <input class="launch-field" name="email" type="email" placeholder="Email" value="{html.escape(hint_email)}" required>
        <input class="launch-field" name="password" type="password" placeholder="Password" value="{html.escape(DEMO_PASSWORD)}" required>
        <button class="launch-btn" type="submit">Sign in</button>
      </form>
      <a class="launch-btn launch-btn-secondary" href="/app/executive">Continue to demo dashboard</a>
      <p class="launch-hint" style="margin-top:16px;">Demo password: <code>{html.escape(DEMO_PASSWORD)}</code></p>
      <div class="launch-role-grid">{''.join(chips)}</div>
      <p class="launch-hint"><a href="/home">Public marketing site</a> · <a href="/demo-landing">Legacy pilot landing</a></p>
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
        + '<div class="launch-card"><h3>Approve / release</h3><p>Placeholder actions — use legacy <a href="/doctor-workbench">doctor workbench</a> for full workflow.</p></div>'
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
