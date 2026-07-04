"""Reception Center web rendering helpers."""

from __future__ import annotations

from flask import session

from app.services import reception_service as svc
from app.web.demo_pilot_lib import metric_cards, page_header, pilot_styles, render_pilot_page

RECEPTION_NAV = (
    ("Dashboard", "/reception"),
    ("Search", "/reception/search"),
    ("Quick Register", "/reception/register/quick"),
    ("Walk-in", "/reception/register/walk-in"),
    ("Check-in", "/reception/check-in"),
    ("Activity Log", "/reception/activity"),
    ("KPI", "/reception/kpi"),
)


def reception_styles() -> str:
    return pilot_styles() + """
    .actions a, .actions button { margin-right:8px; margin-bottom:8px; }
    .actions form { display:inline; }
    .btn { background:#1e3a8a; color:white; border:none; padding:8px 14px; border-radius:8px; cursor:pointer; text-decoration:none; font-size:13px; }
    .btn-secondary { background:#64748b; }
    .btn-success { background:#15803d; }
    .form-grid label { display:block; font-size:13px; color:#475569; margin-bottom:4px; }
    .form-grid input, .form-grid select, .form-grid textarea { width:100%; max-width:420px; padding:10px; border:1px solid #cbd5e1; border-radius:8px; margin-bottom:12px; }
    .flash { background:#ecfdf5; border:1px solid #86efac; color:#166534; padding:12px 16px; border-radius:10px; margin-bottom:16px; }
    .error { background:#fef2f2; border:1px solid #fecaca; color:#991b1b; padding:12px 16px; border-radius:10px; margin-bottom:16px; }
    """


def render_reception_page(title: str, body_html: str) -> str:
    nav = "".join(f'<a href="{href}">{label}</a>' for label, href in RECEPTION_NAV)
    actor = session.get("email", "Reception")
    return f"""
    <html>
    <head>
        <title>{title}</title>
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <style>{reception_styles()}</style>
    </head>
    <body>
        <div class="wrap">
            <div class="nav">{nav}</div>
            <div class="muted" style="margin-bottom:14px;">Signed in as {actor}</div>
            {body_html}
        </div>
    </body>
    </html>
    """


def _queue_table(rows: list[dict], *, actions: bool = True) -> str:
    if not rows:
        return "<p class='muted'>No queue entries.</p>"
    body = ""
    for row in rows:
        action_html = ""
        if actions:
            entry_id = row.get("id", "")
            if row.get("status") == svc.STATUS_WAITING:
                action_html = f"""
                <form method="POST" action="/reception/queue/{entry_id}/check-in" style="display:inline;">
                    <button class="btn btn-success" type="submit">Check In</button>
                </form>
                """
            elif row.get("status") == svc.STATUS_CHECKED_IN:
                action_html = f"""
                <form method="POST" action="/reception/queue/{entry_id}/check-out" style="display:inline;">
                    <button class="btn btn-secondary" type="submit">Check Out</button>
                </form>
                """
        body += f"""
        <tr>
            <td><strong>{row.get('queue_number','')}</strong></td>
            <td>{row.get('patient_id','')}</td>
            <td>{row.get('patient_name','')}</td>
            <td>{row.get('visit_type','')}</td>
            <td>{row.get('status','')}</td>
            <td>{row.get('wait_minutes', 0)} min</td>
            <td>{row.get('payment_status','')}</td>
            <td class="actions">{action_html}</td>
        </tr>
        """
    return f"""
    <table>
        <tr><th>Queue #</th><th>Code</th><th>Name</th><th>Type</th><th>Status</th><th>Wait</th><th>Payment</th><th>Actions</th></tr>
        {body}
    </table>
    """


def build_dashboard_body(*, message: str = "", error: str = "") -> str:
    data = svc.dashboard_payload()
    kpis = data["kpis"]
    flash = ""
    if message:
        flash += f'<div class="flash">{message}</div>'
    if error:
        flash += f'<div class="error">{error}</div>'
    return f"""
    {page_header("Reception Center", "Production reception dashboard for queue, check-in, and registration.")}
    {flash}
    {metric_cards([
        ("Today's Patients", kpis["todays_patients"]),
        ("Waiting Queue", kpis["waiting_queue"]),
        ("Checked-in", kpis["checked_in"]),
        ("Checked-out", kpis["checked_out"]),
        ("Pending Payment", kpis["pending_payment"]),
        ("New Registrations", kpis["new_registrations"]),
    ])}
    <div class="card"><h2>Waiting Queue</h2>{_queue_table(data["waiting_queue"])}</div>
    <div class="card"><h2>Checked-in</h2>{_queue_table(data["checked_in"], actions=True)}</div>
    <div class="card"><h2>Checked-out</h2>{_queue_table(data["checked_out"], actions=False)}</div>
    <div class="card"><h2>Today's New Patients</h2>
    {_patient_table(data["todays_patients"])}
    </div>
    <div class="card"><h2>Upcoming Appointments</h2>
    {_appointment_table(data["upcoming_appointments"])}
    </div>
    """


def _patient_table(patients: list[dict]) -> str:
    if not patients:
        return "<p class='muted'>No new registrations today.</p>"
    rows = "".join(
        f"<tr><td>{p.get('patient_code','')}</td><td>{p.get('full_name','')}</td><td>{p.get('phone','')}</td></tr>"
        for p in patients
    )
    return f"<table><tr><th>Code</th><th>Name</th><th>Phone</th></tr>{rows}</table>"


def _appointment_table(bookings: list[dict]) -> str:
    if not bookings:
        return "<p class='muted'>No appointments scheduled for today.</p>"
    rows = "".join(
        f"<tr><td>{b.get('booking_code','')}</td><td>{b.get('patient_id','')}</td>"
        f"<td>{b.get('service_name','')}</td><td>{b.get('scheduled_at','')}</td><td>{b.get('status','')}</td></tr>"
        for b in bookings
    )
    return f"<table><tr><th>Booking</th><th>Patient</th><th>Service</th><th>When</th><th>Status</th></tr>{rows}</table>"


def build_search_body(*, results: list | None = None, error: str = "") -> str:
    rows = ""
    for patient in results or []:
        rows += f"""
        <tr>
            <td>{patient.patient_code}</td>
            <td>{patient.full_name}</td>
            <td>{patient.phone or ''}</td>
            <td>{patient.national_id or ''}</td>
            <td><a href="/reception/register/walk-in?patient_code={patient.patient_code}">Walk-in</a></td>
        </tr>
        """
    if not rows:
        rows = "<tr><td colspan='5'>No patients found.</td></tr>"
    err = f'<div class="error">{error}</div>' if error else ""
    return f"""
    {page_header("Patient Search", "Search by code, phone, national ID, or name.")}
    {err}
    <div class="card form-grid">
        <form method="GET">
            <label>Patient Code</label><input name="code" placeholder="RC-20260704-0001">
            <label>Phone</label><input name="phone" placeholder="0901234567">
            <label>National ID</label><input name="national_id" placeholder="012345678901">
            <label>Name</label><input name="name" placeholder="Nguyen Van A">
            <button class="btn" type="submit">Search</button>
        </form>
    </div>
    <div class="card"><h2>Results</h2><table><tr><th>Code</th><th>Name</th><th>Phone</th><th>National ID</th><th>Action</th></tr>{rows}</table></div>
    """


def build_quick_register_body(*, message: str = "", error: str = "") -> str:
    flash = f'<div class="flash">{message}</div>' if message else ""
    err = f'<div class="error">{error}</div>' if error else ""
    return f"""
    {page_header("Quick Registration", "Register a new patient with minimal fields and issue a queue number.")}
    {flash}{err}
    <div class="card form-grid">
        <form method="POST">
            <label>Full Name *</label><input name="full_name" required>
            <label>Phone *</label><input name="phone" required>
            <label>Gender</label>
            <select name="gender"><option value="">--</option><option>M</option><option>F</option></select>
            <button class="btn" type="submit">Register & Queue</button>
        </form>
    </div>
    """


def build_walk_in_body(*, message: str = "", error: str = "", defaults: dict | None = None) -> str:
    defaults = defaults or {}
    flash = f'<div class="flash">{message}</div>' if message else ""
    err = f'<div class="error">{error}</div>' if error else ""
    return f"""
    {page_header("Walk-in Registration", "Register or reuse a patient and add them to the waiting queue.")}
    {flash}{err}
    <div class="card form-grid">
        <form method="POST">
            <label>Full Name *</label><input name="full_name" value="{defaults.get('full_name','')}" required>
            <label>Phone *</label><input name="phone" value="{defaults.get('phone','')}" required>
            <label>National ID</label><input name="national_id" value="{defaults.get('national_id','')}">
            <label>Gender</label><select name="gender"><option value="">--</option><option>M</option><option>F</option></select>
            <label>Address</label><textarea name="address">{defaults.get('address','')}</textarea>
            <button class="btn" type="submit">Add to Queue</button>
        </form>
    </div>
    """


def build_check_in_body(*, message: str = "", error: str = "") -> str:
    flash = f'<div class="flash">{message}</div>' if message else ""
    err = f'<div class="error">{error}</div>' if error else ""
    return f"""
    {page_header("Appointment Check-in", "Check in a scheduled appointment and issue queue number.")}
    {flash}{err}
    <div class="card form-grid">
        <form method="POST">
            <label>Booking Code</label><input name="booking_code" placeholder="BK-001">
            <label>Patient Code</label><input name="patient_id" placeholder="DEMO-PAT-001">
            <button class="btn" type="submit">Check In Appointment</button>
        </form>
    </div>
    """


def build_activity_body() -> str:
    rows = ""
    for item in svc.recent_activity(50):
        rows += f"""
        <tr>
            <td>{item.created_at or ''}</td>
            <td>{item.action}</td>
            <td>{item.patient_id or ''}</td>
            <td>{item.details or ''}</td>
            <td>{item.actor_email or ''}</td>
        </tr>
        """
    if not rows:
        rows = "<tr><td colspan='5'>No activity logged yet.</td></tr>"
    return f"""
    {page_header("Reception Activity Log", "Audit trail for search, registration, queue, and check-in events.")}
    <div class="card"><table><tr><th>When</th><th>Action</th><th>Patient</th><th>Details</th><th>Actor</th></tr>{rows}</table></div>
    """


def build_kpi_body() -> str:
    kpis = svc.get_kpis()
    return f"""
    {page_header("Reception KPI", "Operational metrics for today's reception desk.")}
    {metric_cards([
        ("Today's Patients", kpis["todays_patients"]),
        ("Waiting Queue", kpis["waiting_queue"]),
        ("Checked-in", kpis["checked_in"]),
        ("Checked-out", kpis["checked_out"]),
        ("Pending Payment", kpis["pending_payment"]),
        ("New Registrations", kpis["new_registrations"]),
        ("Queue Entries", kpis["total_queue_entries"]),
        ("Avg Wait (min)", kpis["avg_wait_minutes"]),
    ])}
    """
