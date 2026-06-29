from flask import Blueprint, redirect, request

from app.models.partner import Partner
from app.services.partner_portal_service import (
    PartnerDashboardService,
    PartnerOrderService,
    PartnerPortalError,
    PartnerResultUploadService,
    PartnerRevenueService,
    PartnerSLAService,
)


partner_portal_web_bp = Blueprint("partner_portal_web", __name__)


def _styles():
    return """
    body { margin:0; font-family:Arial,sans-serif; background:#f1f5f9; color:#0f172a; }
    .layout { display:flex; min-height:100vh; }
    .sidebar { width:240px; background:#0a4b5c; color:white; padding:24px; }
    .sidebar a { display:block; color:white; text-decoration:none; padding:12px 0; border-bottom:1px solid rgba(255,255,255,.15); }
    .content { flex:1; padding:32px; }
    .card { background:white; border-radius:12px; padding:24px; box-shadow:0 4px 12px rgba(0,0,0,.08); margin-bottom:24px; }
    .grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(160px,1fr)); gap:16px; }
    .metric { background:#e0f2fe; border-radius:12px; padding:16px; }
    .metric strong { display:block; font-size:24px; }
    table { width:100%; border-collapse:collapse; background:white; border-radius:12px; overflow:hidden; }
    th, td { padding:14px; border-bottom:1px solid #e5e7eb; text-align:left; }
    th { background:#e2e8f0; }
    .btn { background:#0d6efd; color:white; padding:10px 16px; border-radius:8px; text-decoration:none; display:inline-block; }
    """


def _sidebar(partner_id):
    return f"""
    <div class="sidebar">
        <h2>Partner Portal</h2>
        <a href="/partner-portal?partner_id={partner_id}">Dashboard</a>
        <a href="/partner-portal/orders?partner_id={partner_id}">Orders</a>
        <a href="/partner-portal/results?partner_id={partner_id}">Results</a>
        <a href="/partner-portal/revenue?partner_id={partner_id}">Revenue</a>
        <a href="/partner-portal/sla?partner_id={partner_id}">SLA</a>
    </div>
    """


@partner_portal_web_bp.route("/partner-portal")
def partner_portal_home():
    partner_id = request.args.get("partner_id")
    if not partner_id:
        partner = Partner.query.first()
        if not partner:
            return "No partners found"
        return redirect(f"/partner-portal?partner_id={partner.id}")

    dashboard = PartnerDashboardService.get_dashboard(partner_id)
    return f"""
    <html><head><title>Partner Portal</title><style>{_styles()}</style></head><body>
    <div class="layout">{_sidebar(partner_id)}<div class="content">
    <h1>{dashboard["partner"]["display_name"]}</h1>
    <div class="grid">
        <div class="metric"><strong>{dashboard["orders_total"]}</strong>Orders</div>
        <div class="metric"><strong>{dashboard["orders_active"]}</strong>Active</div>
        <div class="metric"><strong>{dashboard["revenue_total"]}</strong>Revenue</div>
        <div class="metric"><strong>{dashboard["bookings_total"]}</strong>Bookings</div>
    </div>
    </div></div></body></html>
    """


@partner_portal_web_bp.route("/partner-portal/orders")
def partner_portal_orders():
    partner_id = request.args.get("partner_id")
    if not partner_id:
        return redirect("/partner-portal")
    orders = PartnerOrderService.list_orders(partner_id)
    rows = "".join(
        f"<tr><td>{o['order_code']}</td><td>{o['patient_name']}</td><td>{o['status']}</td></tr>"
        for o in orders
    )
    return f"""
    <html><head><title>Partner Orders</title><style>{_styles()}</style></head><body>
    <div class="layout">{_sidebar(partner_id)}<div class="content">
    <h1>Orders</h1>
    <table><thead><tr><th>Order</th><th>Patient</th><th>Status</th></tr></thead>
    <tbody>{rows or "<tr><td colspan='3'>No orders</td></tr>"}</tbody></table>
    </div></div></body></html>
    """


@partner_portal_web_bp.route("/partner-portal/results")
def partner_portal_results():
    partner_id = request.args.get("partner_id")
    if not partner_id:
        return redirect("/partner-portal")
    results = PartnerResultUploadService.list_results(partner_id)
    rows = "".join(
        f"<tr><td>{r.file_name}</td><td>{r.file_path}</td><td>{r.created_at}</td></tr>"
        for r in results
    )
    return f"""
    <html><head><title>Partner Results</title><style>{_styles()}</style></head><body>
    <div class="layout">{_sidebar(partner_id)}<div class="content">
    <h1>Results</h1>
    <table><thead><tr><th>File</th><th>Path</th><th>Uploaded</th></tr></thead>
    <tbody>{rows or "<tr><td colspan='3'>No results</td></tr>"}</tbody></table>
    </div></div></body></html>
    """


@partner_portal_web_bp.route("/partner-portal/revenue")
def partner_portal_revenue():
    partner_id = request.args.get("partner_id")
    if not partner_id:
        return redirect("/partner-portal")
    revenue = PartnerRevenueService.get_revenue_summary(partner_id)
    return f"""
    <html><head><title>Partner Revenue</title><style>{_styles()}</style></head><body>
    <div class="layout">{_sidebar(partner_id)}<div class="content">
    <h1>Revenue</h1>
    <div class="grid">
        <div class="metric"><strong>{revenue["gross_revenue"]}</strong>Gross</div>
        <div class="metric"><strong>{revenue["net_revenue"]}</strong>Net</div>
        <div class="metric"><strong>{revenue["invoices_paid"]}</strong>Paid Invoices</div>
    </div>
    </div></div></body></html>
    """


@partner_portal_web_bp.route("/partner-portal/sla")
def partner_portal_sla():
    partner_id = request.args.get("partner_id")
    if not partner_id:
        return redirect("/partner-portal")
    sla = PartnerSLAService.get_sla_summary(partner_id)
    return f"""
    <html><head><title>Partner SLA</title><style>{_styles()}</style></head><body>
    <div class="layout">{_sidebar(partner_id)}<div class="content">
    <h1>SLA</h1>
    <div class="grid">
        <div class="metric"><strong>{sla["sla_compliance_rate"]}%</strong>Compliance</div>
        <div class="metric"><strong>{sla["orders_completed"]}</strong>Completed</div>
        <div class="metric"><strong>{sla["breaches"]}</strong>Breaches</div>
    </div>
    </div></div></body></html>
    """
