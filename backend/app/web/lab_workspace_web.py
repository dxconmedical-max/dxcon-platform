"""Laboratory operational workspace UI — Sprint 007."""

from __future__ import annotations

import html

from flask import Blueprint, request

from app.core.web_authz import web_roles_required
from app.lab_workspace.lis_service import list_connectors, list_failed_imports, list_import_batches
from app.lab_workspace.security import LAB_READ_ROLES
from app.lab_workspace.service import testing_queue, workspace_dashboard
from app.utils.auth import login_required
from app.web.launch_ui_lib import metric_cards, render_page, status_badge, table_section

lab_workspace_web_bp = Blueprint("lab_workspace_web", __name__)

LIS_NAV = (
    ("Overview", "/app/lab/lis"),
    ("Connectors", "/app/lab/lis/connectors"),
    ("Import History", "/app/lab/lis/import-history"),
    ("Failed Imports", "/app/lab/lis/failed-imports"),
    ("Mapping", "/app/lab/lis/mapping"),
    ("Upload", "/app/lab/lis/upload"),
)


def _h(v: str) -> str:
    return html.escape(str(v))


def _lis_nav(active: str = "") -> str:
    links = []
    for label, href in LIS_NAV:
        css = "launch-btn launch-btn-sm" if active in href else "launch-btn-outline launch-btn-sm"
        links.append(f'<a class="{css}" href="{href}">{_h(label)}</a>')
    return '<div class="launch-action-row" style="flex-wrap:wrap;margin-bottom:16px;">' + "".join(links) + "</div>"


def _lab_nav(active: str = "") -> str:
    pages = (
        ("Dashboard", "/app/lab"),
        ("Receive", "/app/lab/receive"),
        ("Accession", "/app/lab/accession"),
        ("Testing", "/app/lab/testing"),
        ("Results", "/app/lab/results"),
        ("QC", "/app/lab/qc"),
        ("Validation", "/app/lab/validation"),
        ("LIS", "/app/lab/lis"),
    )
    links = []
    for label, href in pages:
        css = "launch-btn launch-btn-sm" if active == href else "launch-btn-outline launch-btn-sm"
        links.append(f'<a class="{css}" href="{href}">{_h(label)}</a>')
    return '<div class="launch-action-row" style="flex-wrap:wrap;margin-bottom:16px;">' + "".join(links) + "</div>"


def lab_workspace_body() -> str:
    dash = workspace_dashboard()
    kpis = dash.get("kpis", {})
    cards = metric_cards([
        ("Incoming", kpis.get("incoming", 0)),
        ("Testing", kpis.get("testing", 0)),
        ("Pending Validation", kpis.get("pending_validation", 0)),
        ("Pending Review", kpis.get("pending_review", 0)),
        ("Released Today", kpis.get("released_today", 0)),
        ("Failed LIS Imports", kpis.get("failed_imports", 0)),
    ])
    incoming_rows = [
        [_h(r.get("order_code", "")), _h(r.get("patient_name", "")), status_badge(r.get("status", ""))]
        for r in dash.get("incoming_samples", [])[:10]
    ]
    testing_rows = [
        [_h(r.get("accession_number", "—")), _h(r.get("test_name", "")), status_badge(r.get("status", "waiting"))]
        for r in dash.get("testing_queue", [])[:10]
    ]
    review_rows = [
        [_h(r.get("order_code", "")), _h(r.get("patient_name", "")), status_badge(r.get("approval_status", ""))]
        for r in dash.get("pending_review", [])[:10]
    ]
    return (
        _lab_nav("/app/lab")
        + cards
        + '<div class="reception-workspace-grid">'
        + table_section("Incoming Samples", ["Order", "Patient", "Status"], incoming_rows or [["—", "—", status_badge("none")]])
        + table_section("Testing Queue", ["Accession", "Test", "Status"], testing_rows or [["—", "—", status_badge("none")]])
        + table_section("Pending Doctor Review", ["Order", "Patient", "Status"], review_rows or [["—", "—", status_badge("none")]])
        + "</div>"
        + '<p class="launch-hint">API: <code>/api/v1/lab/workspace</code></p>'
    )


def _simple_page(title: str, path: str, description: str) -> str:
    return (
        _lab_nav(path)
        + f'<div class="launch-card"><h3>{_h(title)}</h3><p>{_h(description)}</p>'
        + f'<p>Use <code>POST /api/v1/lab/workspace{"" if path == "/app/lab" else path.replace("/app/lab", "")}</code> or the business order detail for live actions.</p></div>'
    )


@lab_workspace_web_bp.route("/app/lab")
@login_required
@web_roles_required(*LAB_READ_ROLES)
def lab_workspace():
    return render_page("Laboratory Workspace", lab_workspace_body(), active_nav="/app/lab")


@lab_workspace_web_bp.route("/app/lab/receive")
@login_required
@web_roles_required(*LAB_READ_ROLES)
def lab_receive():
    body = _simple_page("Sample Receive", "/app/lab/receive", "Receive specimens with condition status (acceptable, hemolyzed, rejected, etc.).")
    return render_page("Sample Receive", body, active_nav="/app/lab")


@lab_workspace_web_bp.route("/app/lab/accession")
@login_required
@web_roles_required(*LAB_READ_ROLES)
def lab_accession():
    body = _simple_page("Accession", "/app/lab/accession", "Generate ACC-YYYYMMDD-000001 accession numbers.")
    return render_page("Accession", body, active_nav="/app/lab")


@lab_workspace_web_bp.route("/app/lab/testing")
@login_required
@web_roles_required(*LAB_READ_ROLES)
def lab_testing():
    rows = [[_h(r.get("accession_number", "—")), _h(r.get("test_name", "")), _h(r.get("patient", "")), status_badge(r.get("status", ""))] for r in testing_queue(per_page=30)["data"][:20]]
    body = _lab_nav("/app/lab/testing") + table_section("Testing Queue", ["Accession", "Test", "Patient", "Status"], rows or [["—", "—", "—", status_badge("none")]])
    return render_page("Testing Queue", body, active_nav="/app/lab")


@lab_workspace_web_bp.route("/app/lab/results")
@login_required
@web_roles_required(*LAB_READ_ROLES)
def lab_results():
    body = _simple_page("Manual Result Entry", "/app/lab/results", "Enter result values with abnormal flag engine and Master Data validation.")
    return render_page("Result Entry", body, active_nav="/app/lab")


@lab_workspace_web_bp.route("/app/lab/qc")
@login_required
@web_roles_required(*LAB_READ_ROLES)
def lab_qc():
    body = _simple_page("QC Workflow", "/app/lab/qc", "Mark QC passed/failed; results move to validation or pending review.")
    return render_page("Lab QC", body, active_nav="/app/lab")


@lab_workspace_web_bp.route("/app/lab/validation")
@login_required
@web_roles_required(*LAB_READ_ROLES)
def lab_validation():
    body = _simple_page("Lab Validation", "/app/lab/validation", "Supervisor validates imported and manual results before doctor review.")
    return render_page("Lab Validation", body, active_nav="/app/lab")


@lab_workspace_web_bp.route("/app/lab/lis")
@lab_workspace_web_bp.route("/app/lab/lis/connectors")
@lab_workspace_web_bp.route("/app/lab/lis/import-history")
@lab_workspace_web_bp.route("/app/lab/lis/failed-imports")
@lab_workspace_web_bp.route("/app/lab/lis/mapping")
@lab_workspace_web_bp.route("/app/lab/lis/upload")
@login_required
@web_roles_required(*LAB_READ_ROLES)
def lab_lis_pages():
    path = request.path
    active = path if path != "/app/lab/lis" else "/app/lab/lis"
    if "connectors" in path:
        data = list_connectors().get("data", [])
        rows = [[_h(c.get("connector_code", "")), _h(c.get("connector_name", "")), _h(c.get("connector_type", ""))] for c in data]
        body = _lis_nav(path) + table_section("LIS Connectors", ["Code", "Name", "Type"], rows or [["—", "—", "—"]])
        title = "LIS Connectors"
    elif "import-history" in path:
        batches = list_import_batches()
        rows = [[_h(b.get("batch_code", "")), _h(b.get("import_type", "")), status_badge(b.get("status", "")), str(b.get("success_rows", 0))] for b in batches]
        body = _lis_nav(path) + table_section("Import History", ["Batch", "Type", "Status", "Success"], rows or [["—", "—", status_badge("none"), "0"]])
        title = "Import History"
    elif "failed-imports" in path:
        failed = list_failed_imports()
        rows = [[str(r.get("row_number", "")), _h(r.get("error_reason", "")[:60]), _h(r.get("raw_payload_preview", "")[:40])] for r in failed]
        body = _lis_nav(path) + table_section("Failed Imports", ["Row", "Error", "Preview"], rows or [["—", "—", "—"]])
        title = "Failed LIS Imports"
    elif "upload" in path:
        body = _lis_nav(path) + '<div class="launch-card"><h3>Upload Results</h3><p>POST CSV/JSON to <code>/api/v1/lab/workspace/lis/import/csv</code> or <code>.../json</code></p></div>'
        title = "LIS Upload"
    else:
        body = _lis_nav(path) + '<div class="launch-card"><h3>LIS Integrations</h3><p>Connector registry, CSV/JSON import, mapping rules, and failed import management.</p></div>'
        title = "LIS Integrations"
    if "mapping" in path and "connectors" not in path:
        body = _lis_nav(path) + '<div class="launch-card"><h3>Field Mapping</h3><p>Configure external → DxCon field mappings per connector via API.</p></div>'
        title = "LIS Mapping"
    return render_page(title, body, active_nav="/app/lab")
