"""Doctor portal UI — Sprint 009."""

from __future__ import annotations

import html

from flask import Blueprint, request

from app.core.web_authz import web_roles_required
from app.doctor_portal.security import DOCTOR_PORTAL_READ_ROLES, DOCTOR_PORTAL_WRITE_ROLES
from app.doctor_portal.service import dashboard, patient_profile, report_detail, search_patients
from app.utils.auth import login_required
from app.web.launch_ui_lib import action_grid, metric_cards, render_page, status_badge, table_section
from app.web.portal_layout import DOCTOR_NAV, portal_nav

doctor_portal_workspace_web_bp = Blueprint("doctor_portal_workspace_web", __name__)


def _h(v: str) -> str:
    return html.escape(str(v))


@doctor_portal_workspace_web_bp.route("/app/doctor/dashboard")
@login_required
@web_roles_required(*DOCTOR_PORTAL_READ_ROLES)
def doctor_dashboard_page():
    data = dashboard()
    w = data["widgets"]
    body = (
        portal_nav(DOCTOR_NAV, "/app/doctor/dashboard")
        + action_grid([
            ("Review Queue", "/app/doctor/review", "Pending sign-offs"),
            ("Patient Search", "/app/doctor/patients", "Find patients"),
            ("Reports", "/app/reports", "Clinical reports"),
            ("Critical Results", "/app/reports/critical", "High-priority flags"),
        ])
        + metric_cards([
            ("Today's Patients", w["todays_patients"]),
            ("Pending Reviews", w["pending_reviews"]),
            ("Released Reports", w["released_reports"]),
            ("Critical Results", w["critical_results"]),
            ("Notifications", w["notifications"]),
            ("Revenue", "—"),
        ])
        + f'<div class="launch-card"><h3>Quick Search</h3>'
        + f'<form method="GET" action="/app/doctor/patients"><input name="q" placeholder="Patient, order, report..." class="launch-input" style="width:100%;max-width:400px;"/>'
        + f' <button class="launch-btn launch-btn-sm" type="submit">Search</button></form></div>'
        + table_section(
            "Pending Reviews",
            ["Order", "Patient", "Status", ""],
            [
                [_h(r.get("order_code", "")), _h(r.get("patient_name", "")), status_badge(r.get("report_status", "")), f'<a href="/app/doctor/review/{_h(r.get("order_code", ""))}">Review</a>']
                for r in data.get("pending_reviews", [])[:8]
            ] or [["—", "—", status_badge("none"), "—"]],
        )
    )
    return render_page("Doctor Dashboard", body, active_nav="/app/doctor")


@doctor_portal_workspace_web_bp.route("/app/doctor/patients")
@login_required
@web_roles_required(*DOCTOR_PORTAL_READ_ROLES)
def doctor_patients_search():
    result = search_patients(
        q=request.args.get("q"),
        patient_code=request.args.get("patient_code"),
        phone=request.args.get("phone"),
        order_code=request.args.get("order_code"),
        report_code=request.args.get("report_code"),
    )
    rows = []
    for p in result["data"]:
        code = _h(p.get("patient_code", ""))
        rows.append([
            code,
            _h(p.get("full_name", "")),
            _h(p.get("phone") or "—"),
            f'<a href="/app/doctor/patients/{code}">Profile</a>',
        ])
    body = (
        portal_nav(DOCTOR_NAV, "/app/doctor/patients")
        + f'<form method="GET" class="launch-card"><input name="q" value="{_h(request.args.get("q", ""))}" placeholder="Search..." class="launch-input"/> <button type="submit" class="launch-btn launch-btn-sm">Search</button></form>'
        + table_section("Patients", ["Code", "Name", "Phone", ""], rows or [["—", "—", "—", "—"]])
    )
    return render_page("Patient Search", body, active_nav="/app/doctor")


@doctor_portal_workspace_web_bp.route("/app/doctor/patients/<patient_code>")
@login_required
@web_roles_required(*DOCTOR_PORTAL_READ_ROLES)
def doctor_patient_profile(patient_code: str):
    try:
        detail = patient_profile(patient_code)
    except Exception as exc:
        return render_page("Patient", f'<p>{_h(str(exc))}</p>', active_nav="/app/doctor")
    patient = detail["patient"]
    report_rows = [
        [_h(r["report_code"]), status_badge(r["report_status"]), f'<a href="/app/doctor/reports/{_h(r["report_code"])}">View</a>']
        for r in detail.get("released_reports", [])
    ]
    body = (
        portal_nav(DOCTOR_NAV, "/app/doctor/patients")
        + metric_cards([("Patient", patient["full_name"]), ("Code", patient["patient_code"]), ("Critical", len(detail.get("critical_results", [])))])
        + table_section("Released Reports", ["Report", "Status", ""], report_rows or [["—", status_badge("none"), "—"]])
        + table_section("Laboratory Timeline", ["Type", "Code", "Status"], [
            [_h(e.get("type", "")), _h(e.get("code", "")), status_badge(e.get("status", ""))]
            for e in detail.get("laboratory_timeline", [])[:15]
        ])
    )
    return render_page(f"Patient {patient_code}", body, active_nav="/app/doctor")


@doctor_portal_workspace_web_bp.route("/app/doctor/reports/<report_code>")
@login_required
@web_roles_required(*DOCTOR_PORTAL_READ_ROLES)
def doctor_report_viewer(report_code: str):
    try:
        detail = report_detail(report_code)
    except Exception as exc:
        return render_page("Report", f'<p>{_h(str(exc))}</p>', active_nav="/app/doctor")
    report = detail["report"]
    body = (
        portal_nav(DOCTOR_NAV)
        + f'<a class="launch-btn-outline launch-btn-sm" href="/app/reports/{_h(report_code)}/preview">Preview</a> '
        + f'<a class="launch-btn-outline launch-btn-sm" href="/app/reports/{_h(report_code)}/versions">Versions</a> '
        + f'<a class="launch-btn-outline launch-btn-sm" href="/app/reports/{_h(report_code)}/audit">Audit</a>'
        + f'<div class="launch-card report-preview">{report.get("html_content") or "<p>Report content</p>"}</div>'
    )
    return render_page(f"Report {report_code}", body, active_nav="/app/doctor")
