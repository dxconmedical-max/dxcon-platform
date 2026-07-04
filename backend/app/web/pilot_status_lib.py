"""Pilot Status web rendering helpers — Phase 5 Sprint 5.6."""

from __future__ import annotations

import html

from app.services import pilot_status_service as svc
from app.web.demo_pilot_lib import metric_cards, page_header, pilot_styles, status_class

PILOT_STATUS_NAV = (
    ("Pilot Status", "/pilot-status"),
    ("Clinics", "/pilot-status/clinics"),
    ("Labs", "/pilot-status/labs"),
    ("Collectors", "/pilot-status/collectors"),
    ("Doctors", "/pilot-status/doctors"),
    ("Orders", "/pilot-status/orders"),
    ("Revenue", "/pilot-status/revenue"),
    ("Alerts", "/pilot-status/alerts"),
)


def pilot_status_styles() -> str:
    return pilot_styles() + """
    .flow { background:#0f172a; color:#e2e8f0; padding:16px; border-radius:8px; font-family:monospace; line-height:1.8; text-align:center; margin-bottom:16px; }
    .muted { color:#64748b; font-size:13px; margin-bottom:16px; }
    """


def render_pilot_status_page(title: str, body_html: str) -> str:
    nav = "".join(f'<a href="{href}">{label}</a>' for label, href in PILOT_STATUS_NAV)
    return f"""
    <html>
    <head>
        <title>{title}</title>
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <style>{pilot_status_styles()}</style>
    </head>
    <body>
        <div class="wrap">
            <div class="nav">{nav}</div>
            <div class="muted">Live pilot operations · Phase 5 Sprint 5.6</div>
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


def _status_flow() -> str:
    return """
    <div class="flow">
        Pilot Status<br>
        ↓<br>
        Active Clinics<br>
        ↓<br>
        Active Labs<br>
        ↓<br>
        Collectors Online<br>
        ↓<br>
        Doctors Online<br>
        ↓<br>
        Today's Orders<br>
        ↓<br>
        Today's Revenue<br>
        ↓<br>
        Alerts
    </div>
    """


def build_dashboard_body() -> str:
    data = svc.dashboard_payload()
    overview = svc.pilot_status_overview()
    summary = data["summary"]
    system = overview.get("system", {})
    cards = metric_cards(
        [
            ("Active Clinics", summary["active_clinics"]),
            ("Active Labs", summary["active_labs"]),
            ("Collectors Online", summary["collectors_online"]),
            ("Doctors Online", summary["doctors_online"]),
            ("Today's Orders", summary["todays_orders"]),
            ("Today's Revenue", f"{summary['todays_revenue']:,.0f}"),
            ("Open Alerts", summary["alerts_open"]),
        ]
    )
    features = "".join(f"<li>{item}</li>" for item in data["features"])
    return f"""
    {page_header("Pilot Status", "Real-time pilot operations across clinics, labs, field staff, and revenue.")}
    {_status_flow()}
    <div class="card"><strong>Status:</strong> <span class="{status_class(data['status'])}">{html.escape(data['status'])}</span></div>
    {cards}
    <div class="card"><h3>System</h3><p>API: {html.escape(system.get('status', 'UNKNOWN'))} · DB: {html.escape(system.get('database', 'UNKNOWN'))} · Redis: {html.escape(system.get('redis', 'UNKNOWN'))}</p></div>
    <div class="card"><h3>Features</h3><ul>{features}</ul></div>
    """


def build_clinics_body() -> str:
    data = svc.active_clinics()
    rows = [
        [
            html.escape(str(item.get("clinic_code", ""))),
            html.escape(str(item.get("name", ""))),
            html.escape(str(item.get("status", ""))),
        ]
        for item in data.get("clinics", [])
    ]
    return f"""
    {page_header("Active Clinics", "Clinic partners live on the pilot platform.")}
    <div class="card"><p>Active clinics: <strong>{data.get('count', 0)}</strong></p></div>
    <div class="card"><h3>Clinic Registry</h3>{_table(["Code", "Name", "Status"], rows)}</div>
    """


def build_labs_body() -> str:
    data = svc.active_labs()
    rows = [
        [
            html.escape(str(item.get("code", ""))),
            html.escape(str(item.get("name", ""))),
            "Yes" if item.get("is_active") else "No",
        ]
        for item in data.get("labs", [])
    ]
    return f"""
    {page_header("Active Labs", "Laboratory partners processing pilot orders.")}
    <div class="card"><p>Active labs: <strong>{data.get('count', 0)}</strong></p></div>
    <div class="card"><h3>Laboratory Registry</h3>{_table(["Code", "Name", "Active"], rows)}</div>
    """


def build_collectors_body() -> str:
    data = svc.collectors_online()
    rows = [
        [
            html.escape(str(item.get("driver_code", ""))),
            html.escape(str(item.get("full_name", ""))),
            html.escape(str(item.get("status", ""))),
        ]
        for item in data.get("collectors", [])
    ]
    return f"""
    {page_header("Collectors Online", "Field collectors available for sample pickup.")}
    <div class="card"><p>Collectors online: <strong>{data.get('count', 0)}</strong></p></div>
    <div class="card"><h3>Collector Roster</h3>{_table(["Code", "Name", "Status"], rows)}</div>
    """


def build_doctors_body() -> str:
    data = svc.doctors_online()
    rows = [
        [
            html.escape(str(item.get("doctor_code", ""))),
            html.escape(str(item.get("full_name", item.get("name", "")))),
            html.escape(str(item.get("specialty", ""))),
        ]
        for item in data.get("doctors", [])
    ]
    return f"""
    {page_header("Doctors Online", "Clinicians available for result review and sign-off.")}
    <div class="card"><p>Doctors online: <strong>{data.get('count', 0)}</strong></p></div>
    <div class="card"><h3>Doctor Roster</h3>{_table(["Code", "Name", "Specialty"], rows)}</div>
    """


def build_orders_body() -> str:
    data = svc.todays_orders()
    rows = [
        [
            html.escape(str(item.get("order_code", item.get("id", "")))),
            html.escape(str(item.get("status", ""))),
            html.escape(str(item.get("total_amount", ""))),
        ]
        for item in data.get("orders", [])
    ]
    return f"""
    {page_header("Today's Orders", "Orders created during the current pilot day.")}
    <div class="card"><p>Today's orders: <strong>{data.get('count', 0)}</strong></p></div>
    <div class="card"><h3>Order Feed</h3>{_table(["Order", "Status", "Amount"], rows)}</div>
    """


def build_revenue_body() -> str:
    data = svc.todays_revenue()
    exec_metrics = data.get("executive_metrics", {})
    return f"""
    {page_header("Today's Revenue", "Pilot revenue captured today.")}
    <div class="card"><p>Today's revenue: <strong>{data.get('amount', 0):,.0f} {html.escape(data.get('currency', 'VND'))}</strong></p></div>
    <div class="card"><p>Executive dashboard revenue: {exec_metrics.get('today_revenue', 0):,.0f}</p>
    <p>Executive dashboard orders: {exec_metrics.get('today_orders', 0)}</p></div>
    """


def build_alerts_body() -> str:
    data = svc.pilot_alerts()
    rows = [
        [
            html.escape(str(item.get("alert_code", ""))),
            html.escape(str(item.get("severity", ""))),
            html.escape(str(item.get("alert_type", ""))),
            html.escape(str(item.get("message", ""))[:80]),
        ]
        for item in data.get("alerts", [])
    ]
    return f"""
    {page_header("Alerts", "Open operational and clinical alerts requiring attention.")}
    <div class="card"><p>Open alerts: <strong>{data.get('open_count', 0)}</strong></p></div>
    <div class="card"><h3>Alert Queue</h3>{_table(["Code", "Severity", "Type", "Message"], rows)}</div>
    <div class="card"><p>Legacy alert center: <a href="/alerts">/alerts</a></p></div>
    """
