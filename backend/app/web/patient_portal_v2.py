from flask import Blueprint, redirect, request

from app.models.patient import Patient
from app.services.patient_portal_service import (
    MedicalHistoryService,
    PatientDashboardService,
    PatientPortalError,
    TimelineService,
)


patient_portal_v2_web_bp = Blueprint("patient_portal_v2_web", __name__)


def _styles():
    return """
    body { margin:0; font-family:Arial,sans-serif; background:#f8fafc; color:#0f172a; }
    .layout { display:flex; min-height:100vh; }
    .sidebar { width:220px; background:#155e75; color:white; padding:24px; }
    .sidebar a { display:block; color:white; text-decoration:none; padding:12px 0; border-bottom:1px solid rgba(255,255,255,.12); }
    .content { flex:1; padding:32px; }
    .card { background:white; border-radius:12px; padding:24px; box-shadow:0 4px 12px rgba(0,0,0,.08); margin-bottom:24px; }
    .grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(160px,1fr)); gap:16px; }
    .metric { background:#e0f2fe; border-radius:12px; padding:16px; }
    .metric strong { display:block; font-size:24px; }
    table { width:100%; border-collapse:collapse; }
    th, td { padding:12px; border-bottom:1px solid #e5e7eb; text-align:left; font-size:14px; }
    th { background:#e2e8f0; }
    """


def _sidebar(patient_id, active):
    links = [
        ("/patient", "Dashboard"),
        ("/patient/profile", "Profile"),
        ("/patient/results", "Results"),
        ("/patient/orders", "Orders"),
        ("/patient/timeline", "Timeline"),
    ]
    items = ""
    for href, label in links:
        style = ' style="font-weight:bold;"' if href == active else ""
        items += f'<a href="{href}?patient_id={patient_id}"{style}>{label}</a>'
    return f'<div class="sidebar"><h2>Patient Portal</h2>{items}</div>'


def _resolve_patient_id():
    patient_id = request.args.get("patient_id")
    if not patient_id:
        patient = Patient.query.first()
        if not patient:
            return None, "No patients found"
        return patient.id, None
    return patient_id, None


@patient_portal_v2_web_bp.route("/patient")
def patient_home():
    patient_id, error = _resolve_patient_id()
    if error:
        return error
    if not request.args.get("patient_id"):
        return redirect(f"/patient?patient_id={patient_id}")

    try:
        dashboard = PatientDashboardService.get_dashboard(patient_id)
    except PatientPortalError as exc:
        return exc.message, exc.status_code

    summary = dashboard["summary"]
    return f"""
    <html><head><title>Patient Portal</title><style>{_styles()}</style></head><body>
    <div class="layout">{_sidebar(patient_id, "/patient")}<div class="content">
    <div class="card"><h1>{dashboard["patient"]["full_name"]}</h1>
    <div class="grid">
        <div class="metric"><span>Appointments</span><strong>{summary["appointments_total"]}</strong></div>
        <div class="metric"><span>Orders</span><strong>{summary["orders_total"]}</strong></div>
        <div class="metric"><span>Results</span><strong>{summary["results_total"]}</strong></div>
        <div class="metric"><span>Released</span><strong>{summary["released_results_total"]}</strong></div>
    </div></div>
    </div></div></body></html>
    """


@patient_portal_v2_web_bp.route("/patient/profile")
def patient_profile_page():
    patient_id, error = _resolve_patient_id()
    if error:
        return error
    profile = MedicalHistoryService.get_profile(patient_id)
    qr = profile["qr_profile"]
    return f"""
    <html><head><title>Patient Profile</title><style>{_styles()}</style></head><body>
    <div class="layout">{_sidebar(patient_id, "/patient/profile")}<div class="content">
    <div class="card"><h1>Profile</h1>
    <p>Phone: {profile["patient"].get("phone", "")}</p>
    <p>Email: {profile["patient"].get("email", "")}</p>
    <p>QR Code: {qr.get("qr_code", "")}</p>
    <p>Family Members: {len(profile.get("family_members", []))}</p>
    <p>Favorite Doctors: {len(profile.get("favorite_doctors", []))}</p>
    </div></div></div></body></html>
    """


@patient_portal_v2_web_bp.route("/patient/results")
def patient_results_page():
    patient_id, error = _resolve_patient_id()
    if error:
        return error
    results = MedicalHistoryService.list_results(patient_id)
    rows = ""
    for item in results.get("results", [])[:20]:
        code = item.get("result_code") or item.get("order_code") or item.get("source", "")
        status = item.get("status") or ""
        rows += f"<tr><td>{code}</td><td>{status}</td><td>{item.get('download_url', '')}</td></tr>"
    return f"""
    <html><head><title>Patient Results</title><style>{_styles()}</style></head><body>
    <div class="layout">{_sidebar(patient_id, "/patient/results")}<div class="content">
    <div class="card"><h1>Results</h1>
    <table><tr><th>Code</th><th>Status</th><th>Download</th></tr>{rows or "<tr><td colspan='3'>No results</td></tr>"}</table>
    </div></div></div></body></html>
    """


@patient_portal_v2_web_bp.route("/patient/orders")
def patient_orders_page():
    patient_id, error = _resolve_patient_id()
    if error:
        return error
    orders = MedicalHistoryService.list_orders(patient_id)
    rows = ""
    for item in orders.get("orders", [])[:20]:
        rows += f"<tr><td>{item.get('order_code', '')}</td><td>{item.get('status', '')}</td><td>{item.get('order_type', '')}</td></tr>"
    return f"""
    <html><head><title>Patient Orders</title><style>{_styles()}</style></head><body>
    <div class="layout">{_sidebar(patient_id, "/patient/orders")}<div class="content">
    <div class="card"><h1>Orders</h1>
    <table><tr><th>Code</th><th>Status</th><th>Type</th></tr>{rows or "<tr><td colspan='3'>No orders</td></tr>"}</table>
    </div></div></div></body></html>
    """


@patient_portal_v2_web_bp.route("/patient/timeline")
def patient_timeline_page():
    patient_id, error = _resolve_patient_id()
    if error:
        return error
    timeline = TimelineService.get_timeline(patient_id)
    rows = ""
    for item in timeline.get("timeline", [])[:30]:
        rows += f"<tr><td>{item.get('occurred_at', '')}</td><td>{item.get('event_type', '')}</td><td>{item.get('title', '')}</td><td>{item.get('status', '')}</td></tr>"
    return f"""
    <html><head><title>Patient Timeline</title><style>{_styles()}</style></head><body>
    <div class="layout">{_sidebar(patient_id, "/patient/timeline")}<div class="content">
    <div class="card"><h1>Timeline</h1>
    <table><tr><th>When</th><th>Type</th><th>Title</th><th>Status</th></tr>{rows or "<tr><td colspan='4'>No events</td></tr>"}</table>
    </div></div></div></body></html>
    """
