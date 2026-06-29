from flask import Blueprint, redirect, request

from app.models.clinic_profile import ClinicProfile
from app.services.clinic_portal_service import (
    ClinicBookingService,
    ClinicDashboardService,
    ClinicOrderService,
    ClinicPortalError,
    ClinicPortalService,
    ClinicRevenueService,
)


clinic_portal_v2_web_bp = Blueprint("clinic_portal_v2_web", __name__)


def _styles():
    return """
    body { margin:0; font-family:Arial,sans-serif; background:#f8fafc; color:#0f172a; }
    .layout { display:flex; min-height:100vh; }
    .sidebar { width:220px; background:#065f46; color:white; padding:24px; }
    .sidebar a { display:block; color:white; text-decoration:none; padding:12px 0; border-bottom:1px solid rgba(255,255,255,.12); }
    .content { flex:1; padding:32px; }
    .card { background:white; border-radius:12px; padding:24px; box-shadow:0 4px 12px rgba(0,0,0,.08); margin-bottom:24px; }
    .grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(160px,1fr)); gap:16px; }
    .metric { background:#d1fae5; border-radius:12px; padding:16px; }
    .metric strong { display:block; font-size:24px; }
    table { width:100%; border-collapse:collapse; }
    th, td { padding:12px; border-bottom:1px solid #e5e7eb; text-align:left; font-size:14px; }
    th { background:#e2e8f0; }
    """


def _sidebar(clinic_id, active):
    links = [
        ("/clinic/dashboard", "Dashboard"),
        ("/clinic/bookings", "Bookings"),
        ("/clinic/orders", "Orders"),
        ("/clinic/patients", "Patients"),
        ("/clinic/revenue", "Revenue"),
    ]
    items = ""
    for href, label in links:
        style = ' style="font-weight:bold;"' if href == active else ""
        items += f'<a href="{href}?clinic_id={clinic_id}"{style}>{label}</a>'
    return f'<div class="sidebar"><h2>Clinic Portal</h2>{items}</div>'


def _resolve_clinic_id():
    clinic_id = request.args.get("clinic_id")
    if not clinic_id:
        profile = ClinicProfile.query.first()
        if not profile:
            return None, "No clinics found"
        return profile.clinic_id, None
    return clinic_id, None


@clinic_portal_v2_web_bp.route("/clinic")
def clinic_home():
    clinic_id, error = _resolve_clinic_id()
    if error:
        return error
    return redirect(f"/clinic/dashboard?clinic_id={clinic_id}")


@clinic_portal_v2_web_bp.route("/clinic/dashboard")
def clinic_dashboard_page():
    clinic_id, error = _resolve_clinic_id()
    if error:
        return error
    try:
        dashboard = ClinicDashboardService.get_dashboard(clinic_id)
    except ClinicPortalError as exc:
        return exc.message, exc.status_code

    summary = dashboard["summary"]
    return f"""
    <html><head><title>Clinic Dashboard</title><style>{_styles()}</style></head><body>
    <div class="layout">{_sidebar(clinic_id, "/clinic/dashboard")}<div class="content">
    <div class="card"><h1>{dashboard["clinic"]["name"]}</h1>
    <div class="grid">
        <div class="metric"><span>Patients</span><strong>{summary["patients_total"]}</strong></div>
        <div class="metric"><span>Doctors</span><strong>{summary["doctors_total"]}</strong></div>
        <div class="metric"><span>Bookings</span><strong>{summary["bookings_total"]}</strong></div>
        <div class="metric"><span>Revenue</span><strong>{summary["revenue_total"]}</strong></div>
    </div></div>
    </div></div></body></html>
    """


@clinic_portal_v2_web_bp.route("/clinic/bookings")
def clinic_bookings_page():
    clinic_id, error = _resolve_clinic_id()
    if error:
        return error
    bookings = ClinicBookingService.list_bookings(clinic_id)
    rows = ""
    for item in bookings.get("bookings", [])[:20]:
        rows += f"<tr><td>{item.get('booking_code', '')}</td><td>{item.get('service_name', '')}</td><td>{item.get('status', '')}</td></tr>"
    return f"""
    <html><head><title>Clinic Bookings</title><style>{_styles()}</style></head><body>
    <div class="layout">{_sidebar(clinic_id, "/clinic/bookings")}<div class="content">
    <div class="card"><h1>Bookings</h1>
    <table><tr><th>Code</th><th>Service</th><th>Status</th></tr>{rows or "<tr><td colspan='3'>No bookings</td></tr>"}</table>
    </div></div></div></body></html>
    """


@clinic_portal_v2_web_bp.route("/clinic/orders")
def clinic_orders_page():
    clinic_id, error = _resolve_clinic_id()
    if error:
        return error
    orders = ClinicOrderService.list_orders(clinic_id)
    rows = ""
    for item in orders.get("orders", [])[:20]:
        rows += f"<tr><td>{item.get('order_code', '')}</td><td>{item.get('total_amount', 0)}</td><td>{item.get('status', '')}</td></tr>"
    return f"""
    <html><head><title>Clinic Orders</title><style>{_styles()}</style></head><body>
    <div class="layout">{_sidebar(clinic_id, "/clinic/orders")}<div class="content">
    <div class="card"><h1>Orders</h1>
    <table><tr><th>Code</th><th>Amount</th><th>Status</th></tr>{rows or "<tr><td colspan='3'>No orders</td></tr>"}</table>
    </div></div></div></body></html>
    """


@clinic_portal_v2_web_bp.route("/clinic/patients")
def clinic_patients_page():
    clinic_id, error = _resolve_clinic_id()
    if error:
        return error
    patients = ClinicPortalService.list_patients(clinic_id)
    rows = ""
    for item in patients.get("patients", []):
        patient = item.get("patient", {})
        rows += f"<tr><td>{patient.get('full_name', '')}</td><td>{patient.get('phone', '')}</td><td>{item.get('status', '')}</td></tr>"
    return f"""
    <html><head><title>Clinic Patients</title><style>{_styles()}</style></head><body>
    <div class="layout">{_sidebar(clinic_id, "/clinic/patients")}<div class="content">
    <div class="card"><h1>Patients</h1>
    <table><tr><th>Name</th><th>Phone</th><th>Status</th></tr>{rows or "<tr><td colspan='3'>No patients</td></tr>"}</table>
    </div></div></div></body></html>
    """


@clinic_portal_v2_web_bp.route("/clinic/revenue")
def clinic_revenue_page():
    clinic_id, error = _resolve_clinic_id()
    if error:
        return error
    revenue = ClinicRevenueService.get_revenue_summary(clinic_id)
    summary = revenue.get("summary", {})
    return f"""
    <html><head><title>Clinic Revenue</title><style>{_styles()}</style></head><body>
    <div class="layout">{_sidebar(clinic_id, "/clinic/revenue")}<div class="content">
    <div class="card"><h1>Revenue</h1>
    <div class="grid">
        <div class="metric"><span>Gross</span><strong>{summary.get("gross_amount", 0)}</strong></div>
        <div class="metric"><span>Net</span><strong>{summary.get("net_amount", 0)}</strong></div>
        <div class="metric"><span>Orders</span><strong>{summary.get("orders_count", 0)}</strong></div>
    </div></div>
    </div></div></body></html>
    """
