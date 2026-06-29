from flask import Blueprint, redirect, request

from app.models.doctor_profile import DoctorProfile
from app.services.doctor_portal_service import (
    DoctorDashboardService,
    DoctorPatientService,
    DoctorPortalError,
    DoctorReferralService,
)


doctor_portal_v2_web_bp = Blueprint("doctor_portal_v2_web", __name__)


def _styles():
    return """
    body { margin:0; font-family:Arial,sans-serif; background:#f8fafc; color:#0f172a; }
    .layout { display:flex; min-height:100vh; }
    .sidebar { width:220px; background:#1e3a8a; color:white; padding:24px; }
    .sidebar a { display:block; color:white; text-decoration:none; padding:12px 0; border-bottom:1px solid rgba(255,255,255,.12); }
    .content { flex:1; padding:32px; }
    .card { background:white; border-radius:12px; padding:24px; box-shadow:0 4px 12px rgba(0,0,0,.08); margin-bottom:24px; }
    .grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(160px,1fr)); gap:16px; }
    .metric { background:#dbeafe; border-radius:12px; padding:16px; }
    .metric strong { display:block; font-size:24px; }
    table { width:100%; border-collapse:collapse; }
    th, td { padding:12px; border-bottom:1px solid #e5e7eb; text-align:left; font-size:14px; }
    th { background:#e2e8f0; }
    """


def _sidebar(doctor_id, active):
    links = [
        ("/doctor/dashboard", "Dashboard"),
        ("/doctor/patients", "Patients"),
        ("/doctor/results", "Results"),
        ("/doctor/referrals", "Referrals"),
    ]
    items = ""
    for href, label in links:
        style = ' style="font-weight:bold;"' if href == active else ""
        items += f'<a href="{href}?doctor_id={doctor_id}"{style}>{label}</a>'
    return f'<div class="sidebar"><h2>Doctor Portal</h2>{items}</div>'


def _resolve_doctor_id():
    doctor_id = request.args.get("doctor_id")
    if not doctor_id:
        profile = DoctorProfile.query.first()
        if not profile:
            return None, "No doctors found"
        return profile.doctor_id, None
    return doctor_id, None


@doctor_portal_v2_web_bp.route("/doctor")
def doctor_home():
    doctor_id, error = _resolve_doctor_id()
    if error:
        return error
    return redirect(f"/doctor/dashboard?doctor_id={doctor_id}")


@doctor_portal_v2_web_bp.route("/doctor/dashboard")
def doctor_dashboard_page():
    doctor_id, error = _resolve_doctor_id()
    if error:
        return error

    try:
        dashboard = DoctorDashboardService.get_dashboard(doctor_id)
    except DoctorPortalError as exc:
        return exc.message, exc.status_code

    summary = dashboard["summary"]
    return f"""
    <html><head><title>Doctor Dashboard</title><style>{_styles()}</style></head><body>
    <div class="layout">{_sidebar(doctor_id, "/doctor/dashboard")}<div class="content">
    <div class="card"><h1>{dashboard["doctor"]["full_name"]}</h1>
    <div class="grid">
        <div class="metric"><span>Patients</span><strong>{summary["patients_total"]}</strong></div>
        <div class="metric"><span>Referrals</span><strong>{summary["referrals_total"]}</strong></div>
        <div class="metric"><span>Follow-ups</span><strong>{summary["follow_ups_pending"]}</strong></div>
        <div class="metric"><span>Results</span><strong>{summary["released_results_total"]}</strong></div>
    </div></div>
    </div></div></body></html>
    """


@doctor_portal_v2_web_bp.route("/doctor/patients")
def doctor_patients_page():
    doctor_id, error = _resolve_doctor_id()
    if error:
        return error
    patients = DoctorPatientService.list_patients(doctor_id)
    rows = ""
    for item in patients.get("patients", []):
        patient = item.get("patient", {})
        rows += f"<tr><td>{patient.get('full_name', '')}</td><td>{patient.get('phone', '')}</td><td>{item.get('relationship_status', '')}</td></tr>"
    return f"""
    <html><head><title>Doctor Patients</title><style>{_styles()}</style></head><body>
    <div class="layout">{_sidebar(doctor_id, "/doctor/patients")}<div class="content">
    <div class="card"><h1>Patients</h1>
    <table><tr><th>Name</th><th>Phone</th><th>Status</th></tr>{rows or "<tr><td colspan='3'>No patients</td></tr>"}</table>
    </div></div></div></body></html>
    """


@doctor_portal_v2_web_bp.route("/doctor/results")
def doctor_results_page():
    doctor_id, error = _resolve_doctor_id()
    if error:
        return error
    results = DoctorDashboardService.list_results(doctor_id)
    rows = ""
    for item in results.get("results", [])[:20]:
        code = item.get("result_code") or item.get("order_code") or item.get("source", "")
        status = item.get("status") or item.get("result", {}).get("approval_status", "")
        rows += f"<tr><td>{code}</td><td>{status}</td><td>{item.get('review_ready', '')}</td></tr>"
    return f"""
    <html><head><title>Doctor Results</title><style>{_styles()}</style></head><body>
    <div class="layout">{_sidebar(doctor_id, "/doctor/results")}<div class="content">
    <div class="card"><h1>Results</h1>
    <table><tr><th>Code</th><th>Status</th><th>Review Ready</th></tr>{rows or "<tr><td colspan='3'>No results</td></tr>"}</table>
    </div></div></div></body></html>
    """


@doctor_portal_v2_web_bp.route("/doctor/referrals")
def doctor_referrals_page():
    doctor_id, error = _resolve_doctor_id()
    if error:
        return error
    referrals = DoctorReferralService.list_referrals(doctor_id)
    rows = ""
    for item in referrals.get("referrals", [])[:20]:
        rows += f"<tr><td>{item.get('referral_code', '')}</td><td>{item.get('test_name', '')}</td><td>{item.get('status', '')}</td></tr>"
    return f"""
    <html><head><title>Doctor Referrals</title><style>{_styles()}</style></head><body>
    <div class="layout">{_sidebar(doctor_id, "/doctor/referrals")}<div class="content">
    <div class="card"><h1>Referrals</h1>
    <table><tr><th>Code</th><th>Test</th><th>Status</th></tr>{rows or "<tr><td colspan='3'>No referrals</td></tr>"}</table>
    </div></div></div></body></html>
    """
