"""Reception operational workspace UI — Sprint 006."""

from __future__ import annotations

import html

from flask import Blueprint, request, session

from app.core.web_authz import web_roles_required
from app.reception_workspace.security import RECEPTION_READ_ROLES
from app.reception_workspace.service import workspace_dashboard, fast_search_patients
from app.utils.auth import login_required
from app.web.launch_ui_lib import action_grid, metric_cards, render_page, status_badge, table_section

reception_workspace_web_bp = Blueprint("reception_workspace_web", __name__)


def _h(value: str) -> str:
    return html.escape(str(value))


def reception_workspace_body() -> str:
    dash = workspace_dashboard()
    kpis = dash.get("kpis", {})
    kpi_cards = metric_cards([
        ("Today's Patients", kpis.get("todays_patients", 0)),
        ("Today's Revenue", f"${kpis.get('todays_revenue', 0):,.0f}"),
        ("Pending Payments", kpis.get("pending_payments", 0)),
        ("Waiting Collections", kpis.get("waiting_collections", 0)),
    ])

    search_q = request.args.get("q", "")
    search_results = ""
    if search_q:
        result = fast_search_patients(search_q, limit=8)
        rows = [
            [
                f'<a href="/app/patients/{_h(p["patient_code"])}">{_h(p["patient_code"])}</a>',
                _h(p.get("full_name", "")),
                _h(p.get("phone", "")),
            ]
            for p in result["data"]
        ]
        search_results = table_section("Search results", ["Code", "Name", "Phone"], rows or [["—", "—", "—"]])

    queue_rows = []
    for entry in dash.get("workflow_queue", [])[:15]:
        ws = entry.get("workflow_status") or entry.get("status", "WAITING")
        queue_rows.append([
            _h(entry.get("queue_number", "")),
            _h(entry.get("patient_name", entry.get("patient_id", ""))),
            status_badge(ws),
            _h(str(entry.get("wait_minutes", 0)) + " min"),
        ])

    order_rows = []
    for order in dash.get("recent_orders", [])[:8]:
        code = _h(order.get("order_code", ""))
        order_rows.append([
            f'<a href="/app/orders/{code}">{code}</a>',
            _h(order.get("patient_name", "")),
            status_badge(order.get("status", "draft")),
        ])

    patient_rows = []
    for p in dash.get("recent_patients", [])[:8]:
        code = _h(p.get("patient_code", ""))
        patient_rows.append([
            f'<a href="/app/patients/{code}">{_h(p.get("full_name", ""))}</a>',
            _h(p.get("phone", "")),
        ])

    workspace_actions = action_grid([
        ("Search patient", "/app/patients", "Find existing records"),
        ("New registration", "/app/patients/new", "Register walk-in"),
        ("Create order", "/app/orders/new", "New diagnostic order"),
        ("Queue", "/app/reception/queue", "Waiting tokens"),
        ("Pending payment", "/app/finance", "Outstanding invoices"),
    ])
    quick_actions = """
    <div class="launch-action-row reception-quick-actions">
      <a class="launch-btn launch-btn-sm" href="/app/patients/new">New Patient</a>
      <a class="launch-btn launch-btn-sm" href="/app/orders/new">New Order</a>
      <a class="launch-btn-outline launch-btn-sm" href="/app/finance">Collect Payment</a>
      <a class="launch-btn-outline launch-btn-sm" href="/app/reception/queue">Queue</a>
      <a class="launch-btn-outline launch-btn-sm" href="/reception">Reception Center</a>
    </div>
    """

    search_form = f"""
    <form class="launch-card reception-search" method="get" action="/app/reception">
      <h4>Patient Search</h4>
      <input type="search" name="q" value="{_h(search_q)}" placeholder="Code, name, phone, national ID, QR…" autofocus />
      <button type="submit" class="launch-btn launch-btn-sm">Search</button>
    </form>
    """

    layout = f"""
    <div class="reception-workspace">
      {workspace_actions}
      {kpi_cards}
      <div class="reception-workspace-grid">
        <div class="reception-col-left">{search_form}{search_results}</div>
        <div class="reception-col-center">
          {table_section("Today's Queue", ["Token", "Patient", "Status", "Wait"], queue_rows or [["—", "—", status_badge("none"), "—"]])}
          {table_section("Orders Waiting Payment", ["Order", "Patient", "Status"], order_rows[:5] or [["—", "—", status_badge("none")]])}
        </div>
        <div class="reception-col-right">
          <div class="launch-card"><h4>Quick Actions</h4>{quick_actions}</div>
          {table_section("Recent Patients", ["Patient", "Phone"], patient_rows or [["—", "—"]])}
          {table_section("Recent Orders", ["Order", "Patient", "Status"], order_rows or [["—", "—", status_badge("none")]])}
        </div>
      </div>
      <p class="launch-hint">API: <code>/api/v1/reception/workspace</code> · Keyboard: Tab through search, Enter to submit.</p>
    </div>
    """
    return layout


@reception_workspace_web_bp.route("/app/reception/queue")
@login_required
@web_roles_required(*RECEPTION_READ_ROLES)
def reception_queue_live():
    dash = workspace_dashboard()
    rows = []
    for entry in dash.get("workflow_queue", []):
        ws = entry.get("workflow_status") or entry.get("status", "WAITING")
        rows.append([
            _h(entry.get("queue_number", "")),
            _h(entry.get("patient_name", "")),
            status_badge(ws),
            status_badge(entry.get("payment_status", "PENDING")),
        ])
    body = (
        '<a class="launch-btn-outline launch-btn-sm" href="/app/reception">← Reception Workspace</a>'
        + table_section(
            "Today's Queue",
            ["Token", "Patient", "Workflow", "Payment"],
            rows or [["—", "—", status_badge("none"), status_badge("none")]],
        )
    )
    return render_page("Reception Queue", body, active_nav="/app/reception")


@reception_workspace_web_bp.route("/app/reception")
@login_required
@web_roles_required(*RECEPTION_READ_ROLES)
def reception_workspace():
    return render_page("Reception Workspace", reception_workspace_body(), active_nav="/app/reception")
