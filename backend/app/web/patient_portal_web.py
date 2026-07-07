"""Patient portal UI — Sprint 009."""

from __future__ import annotations

import html
import json

from flask import Blueprint, request, session

from app.core.web_authz import web_roles_required
from app.patient_portal.security import PATIENT_PORTAL_READ_ROLES, PATIENT_PORTAL_WRITE_ROLES
from app.patient_portal.service import (
    PatientPortalError,
    dashboard,
    generate_qr_health_card,
    get_report,
    list_consents,
    list_invoices,
    list_notifications,
    medical_history,
    update_profile,
)
from app.extensions.db import db
from app.utils.auth import login_required
from app.web.launch_ui_data import get_session_patient_portal
from app.web.launch_ui_lib import action_grid, metric_cards, render_page, status_badge, table_section
from app.web.portal_layout import PATIENT_NAV, portal_nav

patient_portal_workspace_web_bp = Blueprint("patient_portal_workspace_web", __name__)


def _h(v: str) -> str:
    return html.escape(str(v))


def _patient_code() -> str | None:
    try:
        portal = get_session_patient_portal()
        return portal["patient"]["patient_code"]
    except Exception:
        return session.get("patient_code")


@patient_portal_workspace_web_bp.route("/app/patient/dashboard")
@login_required
@web_roles_required(*PATIENT_PORTAL_READ_ROLES)
def patient_dashboard_page():
    code = _patient_code()
    try:
        data = dashboard(patient_code=code) if code else dashboard()
    except PatientPortalError:
        portal = get_session_patient_portal()
        data = {"widgets": {"recent_reports": 0, "recent_orders": 0, "invoices": 0, "outstanding_balance": 0, "notifications": 0, "profile_completion": 0}, "recent_reports": portal.get("released_reports", []), "recent_orders": portal.get("orders", []), "invoices": portal.get("invoices", [])}
    w = data.get("widgets", {})
    body = (
        portal_nav(PATIENT_NAV, "/app/patient/dashboard")
        + action_grid([
            ("My Reports", "/app/patient/reports", "Released results"),
            ("Medical History", "/app/patient/history", "Timeline view"),
            ("Invoices", "/app/patient/invoices", "Billing"),
            ("Health Card", "/app/patient/qr", "QR access"),
        ])
        + metric_cards([
            ("Reports", w.get("recent_reports", 0)),
            ("Orders", w.get("recent_orders", 0)),
            ("Invoices", w.get("invoices", 0)),
            ("Balance", w.get("outstanding_balance", 0)),
            ("Notifications", w.get("notifications", 0)),
            ("Profile", f"{w.get('profile_completion', 0)}%"),
        ])
        + table_section("Recent Reports", ["Report", "Status", ""], [
            [_h(r.get("report_code", r.get("result_code", ""))), status_badge("released"), f'<a href="/app/patient/reports/{_h(r.get("report_code", r.get("result_code", "")))}">View</a>']
            for r in data.get("recent_reports", [])[:5]
        ] or [["—", status_badge("none"), "—"]])
    )
    return render_page("Patient Dashboard", body, active_nav="/app/patient")


@patient_portal_workspace_web_bp.route("/app/patient/history")
@login_required
@web_roles_required(*PATIENT_PORTAL_READ_ROLES)
def patient_history_page():
    code = _patient_code()
    try:
        hist = medical_history(patient_code=code) if code else medical_history()
    except PatientPortalError as exc:
        return render_page("History", f'<p>{_h(str(exc))}</p>', active_nav="/app/patient")
    rows = [[_h(e.get("event_type", "")), _h(e.get("title", "")), status_badge(e.get("status", "")), _h(e.get("at") or "—")] for e in hist.get("timeline", [])[:30]]
    body = portal_nav(PATIENT_NAV, "/app/patient/history") + table_section("Medical History", ["Type", "Title", "Status", "Date"], rows or [["—"] * 4])
    return render_page("Medical History", body, active_nav="/app/patient")


@patient_portal_workspace_web_bp.route("/app/patient/reports")
@login_required
@web_roles_required(*PATIENT_PORTAL_READ_ROLES)
def patient_reports_list():
    code = _patient_code()
    try:
        hist = medical_history(patient_code=code) if code else medical_history()
        reports = hist.get("reports", [])
    except PatientPortalError:
        portal = get_session_patient_portal()
        reports = portal.get("released_reports", [])
    rows = [[_h(r.get("report_code", "")), status_badge("released"), f'<a href="/app/patient/reports/{_h(r.get("report_code", ""))}">View</a>'] for r in reports]
    return render_page("My Reports", portal_nav(PATIENT_NAV, "/app/patient/reports") + table_section("Released Reports", ["Report", "Status", ""], rows or [["—", status_badge("none"), "—"]]), active_nav="/app/patient")


@patient_portal_workspace_web_bp.route("/app/patient/reports/<report_code>")
@login_required
@web_roles_required(*PATIENT_PORTAL_READ_ROLES)
def patient_report_viewer(report_code: str):
    code = _patient_code()
    try:
        detail = get_report(report_code, patient_code=code)
    except PatientPortalError as exc:
        return render_page("Report", f'<div class="launch-card launch-alert"><p>{_h(str(exc))}</p></div>', active_nav="/app/patient")
    report = detail["report"]
    body = (
        portal_nav(PATIENT_NAV, "/app/patient/reports")
        + f'<p class="launch-hint">QR: {_h(report.get("qr_payload") or "—")}</p>'
        + f'<div class="launch-card report-preview">{detail.get("html_content") or "<p>Report</p>"}</div>'
    )
    return render_page(f"Report {report_code}", body, active_nav="/app/patient")


@patient_portal_workspace_web_bp.route("/app/patient/orders")
@login_required
@web_roles_required(*PATIENT_PORTAL_READ_ROLES)
def patient_orders_page():
    portal = get_session_patient_portal()
    rows = [[_h(o.get("order_code", "")), _h(str(o.get("created_at", "—"))), status_badge(o.get("status", ""))] for o in portal.get("orders", [])]
    return render_page("My Orders", portal_nav(PATIENT_NAV, "/app/patient/orders") + table_section("Orders", ["Order", "Date", "Status"], rows or [["—"] * 3]), active_nav="/app/patient")


@patient_portal_workspace_web_bp.route("/app/patient/invoices")
@login_required
@web_roles_required(*PATIENT_PORTAL_READ_ROLES)
def patient_invoices_page():
    code = _patient_code()
    try:
        inv = list_invoices(patient_code=code) if code else list_invoices()
        invoices = inv.get("invoices", [])
    except PatientPortalError:
        portal = get_session_patient_portal()
        invoices = portal.get("invoices", [])
    rows = [[_h(i.get("invoice_no", i.get("id", ""))), str(i.get("total_amount", i.get("amount", 0))), status_badge(i.get("status", ""))] for i in invoices]
    return render_page("Invoices", portal_nav(PATIENT_NAV, "/app/patient/invoices") + table_section("Invoices", ["Invoice", "Amount", "Status"], rows or [["—"] * 3]), active_nav="/app/patient")


@patient_portal_workspace_web_bp.route("/app/patient/profile")
@login_required
@web_roles_required(*PATIENT_PORTAL_READ_ROLES)
def patient_profile_page():
    portal = get_session_patient_portal()
    patient = portal["patient"]
    body = (
        portal_nav(PATIENT_NAV, "/app/patient/profile")
        + metric_cards([("Name", patient["full_name"]), ("Code", patient["patient_code"]), ("Phone", patient.get("phone", "—"))])
        + f'<div class="launch-card"><p class="launch-hint">Patient code and medical records cannot be changed here.</p></div>'
    )
    return render_page("My Profile", body, active_nav="/app/patient")


@patient_portal_workspace_web_bp.route("/app/patient/qr")
@login_required
@web_roles_required(*PATIENT_PORTAL_READ_ROLES)
def patient_qr_page():
    code = _patient_code()
    qr_data = None
    if code:
        try:
            qr_data = generate_qr_health_card(patient_code=code)
            db.session.commit()
        except PatientPortalError:
            db.session.rollback()
    if not qr_data:
        portal = get_session_patient_portal()
        qr_data = {"qr_payload": portal.get("qr_payload", ""), "patient_code": portal["patient"]["patient_code"]}
    body = (
        portal_nav(PATIENT_NAV, "/app/patient/qr")
        + f'<div class="launch-card"><h3>QR Health Card</h3><div class="launch-chart">{_h(qr_data.get("qr_payload", ""))}</div>'
        + f'<p class="launch-hint">Verification token embedded — no sensitive clinical data.</p></div>'
    )
    return render_page("QR Health Card", body, active_nav="/app/patient")


@patient_portal_workspace_web_bp.route("/app/patient/notifications")
@login_required
@web_roles_required(*PATIENT_PORTAL_READ_ROLES)
def patient_notifications_page():
    code = _patient_code()
    try:
        notif = list_notifications(patient_code=code) if code else {"data": []}
        rows = [[_h(n.get("title", "")), _h(n.get("channel", "")), status_badge(n.get("status", "")), _h(n.get("created_at") or "—")] for n in notif.get("data", [])]
    except PatientPortalError:
        rows = [["Report released", "IN_APP", status_badge("unread"), "—"]]
    return render_page("Notifications", portal_nav(PATIENT_NAV, "/app/patient/notifications") + table_section("Notifications", ["Title", "Channel", "Status", "Time"], rows or [["—"] * 4]), active_nav="/app/patient")


@patient_portal_workspace_web_bp.route("/app/patient/consent")
@login_required
@web_roles_required(*PATIENT_PORTAL_READ_ROLES)
def patient_consent_page():
    code = _patient_code()
    consents = list_consents(patient_code=code) if code else []
    rows = [[_h(c.get("consent_type", "")), status_badge(c.get("status", "")), _h(c.get("granted_at") or "—")] for c in consents]
    return render_page("Consent", portal_nav(PATIENT_NAV) + table_section("Consent History", ["Type", "Status", "Date"], rows or [["—"] * 3]), active_nav="/app/patient")
