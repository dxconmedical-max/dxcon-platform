"""Launch UI Sprint 1 — shared layout, styles, and safe data helpers."""

from __future__ import annotations

import html
from pathlib import Path
from typing import Any

from flask import current_app, request, session, url_for

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

DEMO_ROLE_DASHBOARDS = {
    "ADMIN": "/app/executive",
    "SUPER_ADMIN": "/app/executive",
    "RECEPTION": "/app/reception",
    "DOCTOR": "/app/doctor",
    "LAB": "/app/lab",
    "LAB_TECHNICIAN": "/app/lab",
    "COLLECTOR": "/app/collector",
    "DRIVER": "/app/collector",
    "PATIENT": "/app/patient",
}


def demo_role_dashboard(role: str) -> str:
    return DEMO_ROLE_DASHBOARDS.get((role or "ADMIN").upper(), "/app/executive")


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


def render_page(title: str, body: str, *, public: bool = False, active_nav: str = "") -> str:
    head = page_head(title)
    if public:
        return f"<!DOCTYPE html><html><head>{head}</head><body class=\"launch-ui\">{body}</body></html>"
    ctx = shell_context()
    nav_items = []
    for label, href, _ in APP_NAV:
        active = "active" if active_nav == href or (not active_nav and title.startswith(label)) else ""
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
    <nav>{nav_html}<a class="launch-nav-muted" href="/home">Marketing</a><a class="launch-nav-muted" href="/login">Login</a><a class="launch-nav-muted" href="/logout">Logout</a></nav></aside>
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


def back_nav(href: str, label: str = "Back") -> str:
    return f'<p class="launch-back"><a class="launch-btn-outline" href="{html.escape(href)}">← {html.escape(label)}</a></p>'


def module_intro(title: str, description: str) -> str:
    return f'<div class="launch-card launch-module-intro"><h3>{html.escape(title)}</h3><p>{html.escape(description)}</p></div>'


def action_grid(actions: list[tuple[str, str, str]]) -> str:
    cards = []
    for label, href, desc in actions:
        cards.append(
            f'<a class="launch-action-card" href="{html.escape(href)}">'
            f"<strong>{html.escape(label)}</strong>"
            f"<span>{html.escape(desc)}</span>"
            f"<em>Open →</em></a>"
        )
    return f'<div class="launch-action-grid">{"".join(cards)}</div>'


def query_string_note() -> str:
    args = request.args
    if not args:
        return ""
    parts = [f"{html.escape(k)}={html.escape(v)}" for k, v in args.items()]
    return f'<div class="launch-card launch-filter-note"><p>Filter: <code>{" & ".join(parts)}</code></p></div>'


def status_badge(status: str) -> str:
    raw = (status or "unknown").upper()
    css = "launch-status"
    ok = {"PAID", "COMPLETED", "RELEASED", "APPROVED", "OK", "PASS", "ACTIVE", "SETTLED"}
    warn = {"PENDING", "WAITING", "DRAFT", "PENDING_REVIEW", "IN_TRANSIT", "TESTING", "PROCESSING", "UNPAID", "SCHEDULED"}
    bad = {"CRITICAL", "FAILED", "HIGH", "ABNORMAL", "CANCELLED"}
    if raw in ok:
        css += " launch-status-ok"
    elif raw in bad:
        css += " launch-status-bad"
    elif raw in warn:
        css += " launch-status-warn"
    return f'<span class="{css}">{html.escape(raw.replace("_", " "))}</span>'


def breadcrumbs(items: list[tuple[str, str]]) -> str:
    parts = [f'<a href="{html.escape(href)}">{html.escape(label)}</a>' for label, href in items]
    return '<nav class="launch-breadcrumbs">' + " <span>/</span> ".join(parts) + "</nav>"


def table_html(title: str, headers: list[str], rows: list[list[str]]) -> str:
    head = "".join(f"<th>{html.escape(h)}</th>" for h in headers)
    body = ""
    for row in rows:
        body += "<tr>" + "".join(f"<td>{cell}</td>" for cell in row) + "</tr>"
    if not body:
        body = f'<tr><td colspan="{len(headers)}"><div class="launch-empty-inline">No records yet · showing demo placeholder</div></td></tr>'
    return f'<div class="launch-card"><h3>{html.escape(title)}</h3><table class="launch-table"><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>'


def empty_state(message: str) -> str:
    return f'<div class="launch-card launch-empty"><p>{html.escape(message)}</p></div>'


def queue_stage_cards(stages: dict[str, int]) -> str:
    cards = []
    for label, count in stages.items():
        cards.append(
            f'<div class="launch-card launch-queue-card"><label>{html.escape(label.replace("_", " ").title())}</label>'
            f"<strong>{count}</strong></div>"
        )
    return f'<div class="launch-grid">{"".join(cards)}</div>'


def timeline_section(title: str, events: list[tuple[str, str]]) -> str:
    items = "".join(
        f'<li><strong>{html.escape(when)}</strong><span>{html.escape(label)}</span></li>' for label, when in events
    )
    return f'<div class="launch-card"><h3>{html.escape(title)}</h3><ol class="launch-timeline">{items}</ol></div>'


def demo_form_card(title: str, fields: list[tuple[str, str]], save_href: str, cancel_href: str) -> str:
    inputs = "".join(
        f'<label class="launch-form-label">{html.escape(label)}</label>'
        f'<input class="launch-field" value="{html.escape(value)}" readonly>'
        for label, value in fields
    )
    return (
        f'<div class="launch-card"><h3>{html.escape(title)}</h3><form>{inputs}'
        f'<div class="launch-footer-actions">'
        f'<a class="launch-btn" href="{html.escape(save_href)}">Save demo</a>'
        f'<a class="launch-btn-outline" href="{html.escape(cancel_href)}">Cancel</a>'
        f"</div></form></div>"
    )


def real_form_card(
    title: str,
    action: str,
    fields: list[tuple[str, str, str]],
    *,
    cancel_href: str,
    submit_label: str = "Save",
    method: str = "POST",
) -> str:
    """Editable form: (name, label, value). Checkbox fields use name test_catalog_id."""
    inputs = []
    for name, label, value in fields:
        if name == "test_catalog_id":
            inputs.append(
                f'<label class="launch-form-label"><input type="checkbox" name="test_catalog_id" '
                f'value="{html.escape(value)}" checked> {html.escape(label)}</label>'
            )
        elif name == "note":
            inputs.append(
                f'<label class="launch-form-label">{html.escape(label)}</label>'
                f'<textarea class="launch-field" name="{html.escape(name)}">{html.escape(value)}</textarea>'
            )
        else:
            inputs.append(
                f'<label class="launch-form-label">{html.escape(label)}</label>'
                f'<input class="launch-field" name="{html.escape(name)}" value="{html.escape(value)}">'
            )
    return (
        f'<div class="launch-card"><h3>{html.escape(title)}</h3>'
        f'<form method="{html.escape(method)}" action="{html.escape(action)}">{"".join(inputs)}'
        f'<div class="launch-footer-actions">'
        f'<button type="submit" class="launch-btn">{html.escape(submit_label)}</button>'
        f'<a class="launch-btn-outline" href="{html.escape(cancel_href)}">Cancel</a>'
        f"</div></form></div>"
    )


def workflow_action_form(action: str, order_ref: str, label: str, fields: list[tuple[str, str, str]] | None = None) -> str:
    hidden = f'<input type="hidden" name="return_to" value="/app/orders/{html.escape(order_ref)}">'
    field_html = ""
    if fields:
        for name, lbl, val in fields:
            field_html += (
                f'<label class="launch-form-label">{html.escape(lbl)}</label>'
                f'<input class="launch-field" name="{html.escape(name)}" value="{html.escape(val)}">'
            )
    return (
        f'<form method="POST" action="{html.escape(action)}" class="launch-inline-form">'
        f"{hidden}{field_html}"
        f'<button type="submit" class="launch-btn launch-btn-sm">{html.escape(label)}</button>'
        f"</form>"
    )


def safe_patient_rows(limit: int = 8) -> list[list[str]]:
    from app.models.patient import Patient

    def fetch():
        rows = []
        for patient in Patient.query.limit(limit).all():
            rows.append([
                patient.full_name or "Demo Patient",
                patient.phone or "—",
                patient.patient_code or "—",
            ])
        return rows

    return _safe(fetch, [["Demo Patient", "0901234567", "P-DEMO-001"], ["Demo Patient 2", "0907654321", "P-DEMO-002"]])


def safe_order_rows(limit: int = 8) -> list[list[str]]:
    from app.models.order import Order

    def fetch():
        rows = []
        for order in Order.query.order_by(Order.created_at.desc()).limit(limit).all():
            code = getattr(order, "order_code", None) or getattr(order, "id", "ORD")
            status = getattr(order, "status", "Processing") or "Processing"
            amount = getattr(order, "total_amount", None) or "—"
            rows.append([str(code), "Demo Patient", str(status), str(amount)])
        return rows

    return _safe(fetch, [["ORD-1001", "Demo Patient", "Processing", "$45"], ["ORD-1002", "Demo Patient 2", "Completed", "$120"]])


def safe_report_rows(limit: int = 8) -> list[list[str]]:
    from app.models.test_result import TestResult

    def fetch():
        rows = []
        for result in TestResult.query.limit(limit).all():
            code = getattr(result, "result_code", None) or getattr(result, "id", "RPT")
            status = getattr(result, "status", "Pending review") or "Pending review"
            rows.append([str(code), "Demo Patient", str(status), "Normal"])
        return rows

    return _safe(fetch, [["RPT-001", "Demo Patient", "Pending review", "High"], ["RPT-002", "Demo Patient 2", "Released", "Critical"]])


def safe_sample_rows(limit: int = 8) -> list[list[str]]:
    from app.models.sample_tracking import SampleTracking

    def fetch():
        rows = []
        for sample in SampleTracking.query.limit(limit).all():
            code = getattr(sample, "sample_code", None) or getattr(sample, "id", "S")
            status = getattr(sample, "status", "Queued") or "Queued"
            rows.append([str(code), "CBC", str(status), "Today"])
        return rows

    return _safe(fetch, [["S-001", "CBC", "Queued", "Today"], ["S-002", "Chem", "Testing", "Today"]])


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
            f'<a class="launch-role-card" href="/login/demo?role={html.escape(label)}">'
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
      <a class="launch-btn launch-btn-secondary" href="/login/demo?role=ADMIN">Continue to demo dashboard</a>
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
    from app.web.launch_ui_data import get_demo_counts, get_recent_orders, get_system_status, get_top_test_categories

    counts = get_demo_counts()
    system = get_system_status()
    modules = action_grid([
        ("Orders", "/app/orders", "View and manage orders"),
        ("Patients", "/app/patients", "Patient directory"),
        ("Reports", "/app/reports", "Results and validation"),
        ("Finance", "/app/finance", "Invoices and payments"),
        ("Logistics", "/app/logistics", "Transport and SLA"),
        ("System", "/app/system", "Health and runbooks"),
    ])
    cards = metric_cards(
        [
            ("Total patients", counts["patients"]),
            ("Total orders", counts["orders"]),
            ("Test catalog", counts["tests"]),
            ("Est. revenue", f"${counts['revenue']:,.0f}"),
            ("Pending reports", counts["pending_reports"]),
            ("Samples in transit", counts["samples_in_transit"]),
            ("System health", system["health"]),
            ("Database", system["database"]),
        ]
    )
    order_rows = []
    for order in get_recent_orders(6):
        key = html.escape(order["order_code"])
        order_rows.append([
            f'<a href="/app/orders/{key}">{key}</a>',
            html.escape(order["patient_name"]),
            status_badge(order["status"]),
            f"${order['total_amount']:,.0f}",
        ])
    categories = get_top_test_categories()
    cat_rows = [[html.escape(c["category"]), str(c["tests"])] for c in categories]
    return (
        modules
        + cards
        + table_html("Recent orders", ["Order", "Patient", "Status", "Amount"], order_rows)
        + table_section("Top test categories", ["Category", "Tests"], cat_rows)
        + metric_cards([("Redis", system["redis"]), ("Environment", system["environment"])])
    )


def reception_dashboard_body() -> str:
    from app.web.launch_ui_actions import action_button, action_button_row
    from app.web.launch_ui_data import get_finance_summary, get_recent_orders, get_recent_patients, get_sample_patient_key

    patient_key = get_sample_patient_key()
    actions = action_grid([
        ("Search patient", "/app/patients", "Find existing records"),
        ("New registration", "/app/patients/new", "Register walk-in"),
        ("Create order", "/app/orders/new", "New diagnostic order"),
        ("Queue", "/app/reception/queue", "Waiting tokens"),
        ("Pending payment", "/app/finance", "Outstanding invoices"),
    ])
    quick_actions = action_button_row([
        action_button("Check in next patient", "check-in-patient", patient_key, "patient", "/app/reception", primary=True),
        action_button("Create quick order", "create-demo-order", patient_key, "order", "/app/reception"),
        action_button("Mark payment received", "mark-paid", "INV-DEMO-001", "invoice", "/app/reception"),
    ])
    patient_rows = []
    for patient in get_recent_patients(4):
        patient_rows.append([html.escape(patient["full_name"]), html.escape(patient["phone"]), "Today"])
    finance = get_finance_summary()
    pending_rows = [[f"INV pending ({finance['pending_count']})", f"${finance['revenue']:,.0f}", status_badge("UNPAID")]]
    order_rows = []
    for order in get_recent_orders(3):
        key = html.escape(order["order_code"])
        order_rows.append([f'<a href="/app/orders/{key}">{key}</a>', html.escape(order["patient_name"]), status_badge(order["status"])])
    return quick_actions + actions + (
        table_html("Quick patient search", ["Patient", "Phone", "Last visit"], patient_rows)
        + table_html("Today queue snapshot", ["Token", "Patient", "Status"], [
            ["Q-101", "Nguyen Van A", status_badge("WAITING")],
            ["Q-102", "Le Van C", status_badge("SAMPLING")],
        ])
        + table_html("Pending payment", ["Invoice", "Amount", "Status"], pending_rows)
        + table_html("Recent orders", ["Order", "Patient", "Status"], order_rows)
    )


def doctor_dashboard_body() -> str:
    from app.web.launch_ui_actions import action_button, action_button_row
    from app.web.launch_ui_data import get_recent_reports, get_sample_report_key

    report_key = get_sample_report_key()
    quick_actions = action_button_row([
        action_button("Review critical result", "doctor-approve", report_key, "report", "/app/doctor", primary=True),
        action_button("Approve report", "doctor-approve", report_key, "report", "/app/doctor"),
    ])
    actions = action_grid([
        ("Pending review", "/app/reports?status=pending_review", "Results awaiting sign-off"),
        ("Critical results", "/app/reports?critical=1", "High-priority flags"),
        ("Patient timeline", "/app/patients", "Longitudinal view"),
        ("AI interpretation", "/app/ai", "Advisory summaries"),
        ("Release report", "/app/reports", "Approve and release"),
    ])
    review_rows = []
    for report in get_recent_reports(4):
        key = html.escape(report["id"])
        review_rows.append([
            html.escape(report["patient_name"]),
            html.escape(report["test_name"]),
            status_badge(report["flag"]),
            f'<a class="launch-btn-outline launch-btn-sm" href="/app/reports/{key}">Review</a>',
        ])
    return quick_actions + actions + table_html("Pending review", ["Patient", "Test", "Flag", "Action"], review_rows)


def lab_dashboard_body() -> str:
    from app.web.launch_ui_actions import action_button, action_button_row
    from app.web.launch_ui_data import get_recent_reports, get_recent_samples, get_sample_order_key

    order_key = get_sample_order_key()
    quick_actions = action_button_row([
        action_button("Receive sample", "receive-sample", order_key, "sample", "/app/lab", primary=True),
        action_button("Start testing", "start-testing", order_key, "sample", "/app/lab"),
        action_button("Complete QC", "complete-qc", "QC-DEMO-01", "qc_run", "/app/lab"),
    ])
    actions = action_grid([
        ("Sample queue", "/app/samples", "Incoming specimens"),
        ("Accession", "/app/samples/accession", "Receive in lab"),
        ("Testing", "/app/lab/testing", "Active analyzers"),
        ("QC", "/app/lab/qc", "Quality control runs"),
        ("Validation", "/app/reports", "Sign-off queue"),
    ])
    sample_rows = []
    for sample in get_recent_samples(5):
        sample_rows.append([
            html.escape(sample["sample_code"]),
            status_badge(sample["status"]),
            html.escape(sample.get("updated_at", "—")),
        ])
    report_rows = []
    for report in get_recent_reports(3):
        key = html.escape(report["id"])
        report_rows.append([html.escape(report["test_name"]), status_badge(report["approval_status"]), f'<a href="/app/reports/{key}">Open</a>'])
    return quick_actions + actions + (
        table_html("Sample queue", ["Sample", "Status", "Updated"], sample_rows)
        + table_html("Validation queue", ["Test", "Status", "Action"], report_rows)
        + metric_cards([("QC today", "2 pass"), ("Analyzers", "3 active")])
    )


def collector_dashboard_body() -> str:
    from app.web.launch_ui_actions import action_button, action_button_row
    from app.web.launch_ui_data import get_demo_counts, get_recent_collections, get_sample_order_key

    order_key = get_sample_order_key()
    quick_actions = action_button_row([
        action_button("Accept pickup", "assign-collector", order_key, "collection", "/app/collector", primary=True),
        action_button("Collect sample", "collect-sample", order_key, "sample", "/app/collector"),
        action_button("Handover sample", "receive-sample", order_key, "sample", "/app/collector"),
    ])
    actions = action_grid([
        ("Pickup queue", "/app/collections", "Today's jobs"),
        ("Route", "/app/collections/route", "Optimized stops"),
        ("GPS / logistics", "/app/logistics", "Fleet overview"),
        ("Cold box temperature", "/app/iot", "IoT monitoring"),
        ("Chain of custody", "/app/samples/chain-of-custody", "Scan history"),
    ])
    counts = get_demo_counts()
    pickup_rows = []
    for job in get_recent_collections(5):
        pickup_rows.append([
            html.escape(job["job_code"]),
            html.escape(job["address"]),
            status_badge(job["status"]),
            html.escape(job["eta"]),
        ])
    return quick_actions + actions + (
        metric_cards([("Samples in transit", counts["samples_in_transit"]), ("Cold boxes", "2 active")])
        + table_html("Pickup queue", ["Job", "Address", "Status", "ETA"], pickup_rows)
        + '<div class="launch-card"><h3>GPS overview</h3><div class="launch-chart">Live map placeholder · <a href="/app/logistics">Open logistics</a></div></div>'
    )


def patient_dashboard_body() -> str:
    from app.web.launch_ui_actions import action_button, action_button_row
    from app.web.launch_ui_data import get_recent_invoices, get_recent_orders, get_recent_reports, get_sample_report_key

    report_key = get_sample_report_key()
    quick_actions = action_button_row([
        action_button("View latest report", "release-report", report_key, "report", "/app/patient", primary=True),
        action_button("Download PDF (demo)", "send-notification", report_key, "report", "/app/patient"),
        action_button("Pay invoice", "mark-paid", "INV-DEMO-001", "invoice", "/app/patient"),
    ])
    actions = action_grid([
        ("My profile", "/app/patient/profile", "Demographics"),
        ("My orders", "/app/patient/orders", "Track diagnostics"),
        ("Reports", "/app/patient/reports", "Released results"),
        ("QR card", "/app/patient/qr", "Check-in code"),
        ("Invoices", "/app/patient/invoices", "Billing"),
        ("Notifications", "/app/patient/notifications", "Alerts inbox"),
    ])
    orders = get_recent_orders(2)
    reports = get_recent_reports(2)
    invoices = get_recent_invoices(2)
    return quick_actions + actions + metric_cards([
        ("Active orders", len(orders)),
        ("New reports", len(reports)),
        ("Open invoices", sum(1 for i in invoices if i.get("status", "").upper() != "PAID")),
    ])


def system_dashboard_body() -> str:
    ctx = shell_context()
    actions = action_grid([
        ("API health", "/health", "Liveness probe"),
        ("Readiness", "/ready", "Deployment readiness"),
        ("Enterprise hub", "/healthcare-ecosystem", "Ecosystem modules"),
        ("Executive view", "/app/executive", "Operations dashboard"),
    ])
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
    return actions + cards + links
