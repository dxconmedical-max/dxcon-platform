"""Reporting engine and doctor review UI — Sprint 008."""

from __future__ import annotations

import html

from flask import Blueprint, request

from app.core.web_authz import web_roles_required
from app.models.clinical_report import ClinicalReport, CriticalResultAlert
from app.reporting_engine.security import DOCTOR_APPROVE_ROLES, REPORT_READ_ROLES
from app.reporting_engine.service import audit_timeline, review_detail, review_queue, search_reports, report_versions
from app.utils.auth import login_required
from app.web.launch_ui_lib import metric_cards, render_page, status_badge, table_section

reporting_engine_web_bp = Blueprint("reporting_engine_web", __name__)


def _h(v: str) -> str:
    return html.escape(str(v))


def _doctor_nav(active: str = "") -> str:
    links = [
        ("Review Queue", "/app/doctor/review"),
        ("Workbench", "/app/doctor"),
        ("Reports", "/app/reports"),
        ("Critical", "/app/reports/critical"),
    ]
    return '<div class="launch-action-row">' + "".join(
        f'<a class="{"launch-btn launch-btn-sm" if href == active else "launch-btn-outline launch-btn-sm"}" href="{href}">{_h(label)}</a>'
        for label, href in links
    ) + "</div>"


@reporting_engine_web_bp.route("/app/doctor/review")
@login_required
@web_roles_required(*DOCTOR_APPROVE_ROLES)
def doctor_review_queue():
    result = review_queue(
        patient=request.args.get("patient"),
        order_code=request.args.get("order_code"),
        critical_only=request.args.get("critical_only") == "1",
        status=request.args.get("status"),
    )
    rows = []
    for r in result["data"]:
        oc = _h(r.get("order_code", ""))
        rows.append([
            _h(r.get("patient_name", "")),
            f'<a href="/app/doctor/review/{oc}">{oc}</a>',
            _h(r.get("accession_number") or "—"),
            str(r.get("test_count", 0)),
            str(r.get("abnormal_count", 0)),
            str(r.get("critical_count", 0)),
            status_badge(r.get("report_status", "pending_review")),
        ])
    body = (
        _doctor_nav("/app/doctor/review")
        + metric_cards([("Queue", len(result["data"])), ("Critical filter", request.args.get("critical_only", "0"))])
        + table_section(
            "Doctor Review Queue",
            ["Patient", "Order", "Accession", "Tests", "Abnormal", "Critical", "Status"],
            rows or [["—", "—", "—", "0", "0", "0", status_badge("none")]],
        )
    )
    return render_page("Doctor Review", body, active_nav="/app/doctor")


@reporting_engine_web_bp.route("/app/doctor/review/<order_ref>")
@login_required
@web_roles_required(*DOCTOR_APPROVE_ROLES)
def doctor_review_detail(order_ref: str):
    try:
        detail = review_detail(order_ref)
    except Exception as exc:
        return render_page("Review", f'<div class="launch-card"><p>{_h(str(exc))}</p></div>', active_nav="/app/doctor")
    report = detail["report"]
    rc = _h(report["report_code"])
    item_rows = [
        [_h(i.get("test_name", "")), _h(str(i.get("result_value", ""))), _h(i.get("unit") or ""), _h(i.get("reference_range") or ""), status_badge(i.get("flag") or "NORMAL")]
        for i in detail.get("result_items", [])
    ]
    timeline = detail.get("audit_timeline", [])
    tl_rows = [[_h(e.get("action", "")), _h(e.get("status") or ""), _h(e.get("time") or "")] for e in timeline[:10]]
    actions = f"""
    <div class="launch-action-row">
      <form method="post" action="/app/business/orders/{_h(order_ref)}/approve" style="display:inline"><input type="hidden" name="doctor_note" value="Approved via review workspace"/><button class="launch-btn launch-btn-sm" type="submit">Approve</button></form>
      <form method="post" action="/app/business/orders/{_h(order_ref)}/release" style="display:inline"><button class="launch-btn-outline launch-btn-sm" type="submit">Release</button></form>
      <a class="launch-btn-outline launch-btn-sm" href="/app/reports/{rc}/preview">Preview Report</a>
      <a class="launch-btn-outline launch-btn-sm" href="/api/v1/reporting/reports/{rc}/pdf">Download PDF</a>
    </div>
    """
    body = (
        _doctor_nav("/app/doctor/review")
        + metric_cards([
            ("Report", report["report_code"]),
            ("Status", report["report_status"]),
            ("Abnormal", detail.get("abnormal_count", 0)),
            ("Critical", detail.get("critical_count", 0)),
        ])
        + f'<div class="launch-card"><h3>Patient</h3><p>{_h(detail["patient_summary"].get("full_name", ""))}</p></div>'
        + actions
        + table_section("Results", ["Test", "Value", "Unit", "Reference", "Flag"], item_rows or [["—"] * 5])
        + table_section("Audit timeline", ["Action", "Status", "Time"], tl_rows or [["—", "—", "—"]])
    )
    return render_page(f"Review {order_ref}", body, active_nav="/app/doctor")


@reporting_engine_web_bp.route("/app/reports")
@login_required
@web_roles_required(*REPORT_READ_ROLES)
def reports_search():
    result = search_reports(
        patient=request.args.get("patient"),
        order_code=request.args.get("order_code"),
        report_code=request.args.get("report_code"),
        status=request.args.get("status"),
    )
    rows = []
    for r in result["data"]:
        rc = _h(r["report_code"])
        rows.append([
            rc,
            _h(r.get("order_code", "")),
            _h(r.get("patient_id", "")),
            status_badge(r.get("report_status", "")),
            f'<a href="/app/reports/{rc}/preview">Preview</a>'
            + (
                f' · <a href="/api/v1/reporting/reports/{rc}/pdf">PDF</a>'
                if r.get("pdf_path") and r.get("report_status") in ("approved", "released", "amended")
                else ""
            ),
        ])
    body = (
        '<div class="launch-action-row"><a class="launch-btn-outline launch-btn-sm" href="/app/doctor/review">Doctor Review</a></div>'
        + table_section("Reports", ["Code", "Order", "Patient", "Status", ""], rows or [["—", "—", "—", status_badge("none"), "—"]])
    )
    return render_page("Reports", body, active_nav="/app/reports")


@reporting_engine_web_bp.route("/app/reports/<report_code>/preview")
@login_required
@web_roles_required(*REPORT_READ_ROLES)
def report_preview(report_code: str):
    report = ClinicalReport.query.filter_by(report_code=report_code).first()
    if not report:
        return render_page("Preview", '<div class="launch-card"><p>Report not found.</p></div>', active_nav="/app/reports")
    html_content = report.html_content or "<p>Report not generated yet.</p>"
    pdf_link = ""
    if report.pdf_path and report.report_status in ("approved", "released", "amended"):
        pdf_link = (
            f'<div class="launch-action-row">'
            f'<a class="launch-btn launch-btn-sm" href="/api/v1/reporting/reports/{_h(report_code)}/pdf">Download PDF</a>'
            f'<form method="post" action="/api/v1/reporting/reports/{_h(report_code)}/reprint" style="display:inline">'
            f'<button class="launch-btn-outline launch-btn-sm" type="submit">Reprint PDF</button></form>'
            f'<button class="launch-btn-outline launch-btn-sm" type="button" onclick="window.print()">Print</button>'
            f'</div>'
        )
    body = (
        f'<a class="launch-btn-outline launch-btn-sm" href="/app/reports">← Reports</a>'
        + pdf_link
        + f'<div class="launch-card report-preview">{html_content}</div>'
        + f'<p class="launch-hint">Hash: <code>{_h(report.report_hash or "—")}</code> · Version {report.report_version}'
        + (f' · PDF ready' if report.pdf_path else ' · PDF pending')
        + '</p>'
    )
    return render_page(f"Report {report_code}", body, active_nav="/app/reports")


@reporting_engine_web_bp.route("/app/reports/<report_code>/versions")
@login_required
@web_roles_required(*REPORT_READ_ROLES)
def report_versions_page(report_code: str):
    versions = report_versions(report_code)
    rows = [[f"v{r.get('version')}", _h(r.get("report_code", "")), status_badge(r.get("report_status", ""))] for r in versions]
    body = table_section("Report Versions", ["Version", "Code", "Status"], rows or [["—", "—", status_badge("none")]])
    return render_page("Versions", body, active_nav="/app/reports")


@reporting_engine_web_bp.route("/app/reports/<report_code>/audit")
@login_required
@web_roles_required(*REPORT_READ_ROLES)
def report_audit_page(report_code: str):
    events = audit_timeline(report_code)
    rows = [[_h(e.get("action", "")), _h(e.get("actor") or ""), _h(e.get("time") or "")] for e in events]
    body = table_section("Audit Timeline", ["Action", "Actor", "Time"], rows or [["—", "—", "—"]])
    return render_page("Audit", body, active_nav="/app/reports")


@reporting_engine_web_bp.route("/app/reports/critical")
@login_required
@web_roles_required(*DOCTOR_APPROVE_ROLES)
def critical_reports():
    alerts = CriticalResultAlert.query.order_by(CriticalResultAlert.created_at.desc()).limit(50).all()
    rows = [[_h(a.order_code or ""), _h(a.critical_type or ""), status_badge(a.status or "new"), _h(a.patient_id)] for a in alerts]
    body = _doctor_nav("/app/reports/critical") + table_section("Critical Results", ["Order", "Type", "Status", "Patient"], rows or [["—", "—", status_badge("none"), "—"]])
    return render_page("Critical Results", body, active_nav="/app/doctor")
