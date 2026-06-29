from flask import Blueprint, request

from app.services.reporting_service import ExecutiveDashboardService, KPIService, ReportingService


reporting_bi_web_bp = Blueprint("reporting_bi_web", __name__)


def _styles():
    return """
    body { margin:0; font-family:Arial,sans-serif; background:#f8fafc; color:#0f172a; }
    .layout { display:flex; min-height:100vh; }
    .sidebar { width:220px; background:#1e293b; color:white; padding:24px; }
    .sidebar a { display:block; color:white; text-decoration:none; padding:12px 0; border-bottom:1px solid rgba(255,255,255,.12); }
    .content { flex:1; padding:32px; }
    .card { background:white; border-radius:12px; padding:24px; box-shadow:0 4px 12px rgba(0,0,0,.08); margin-bottom:24px; }
    .grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(160px,1fr)); gap:16px; }
    .metric { background:#e0f2fe; border-radius:12px; padding:16px; }
    .metric strong { display:block; font-size:24px; }
    table { width:100%; border-collapse:collapse; background:white; border-radius:12px; overflow:hidden; }
    th, td { padding:12px; border-bottom:1px solid #e5e7eb; text-align:left; font-size:14px; }
    th { background:#e2e8f0; }
    """


def _sidebar(active):
    links = [
        ("/reports", "Overview"),
        ("/reports/executive", "Executive"),
        ("/reports/operations", "Operations"),
    ]
    items = ""
    for href, label in links:
        cls = ' style="font-weight:bold;"' if href == active else ""
        items += f'<a href="{href}"{cls}>{label}</a>'
    return f'<div class="sidebar"><h2>Reports</h2>{items}</div>'


def _metric_cards(metrics):
    cards = ""
    for label, value in metrics:
        cards += f'<div class="metric"><span>{label}</span><strong>{value}</strong></div>'
    return f'<div class="grid">{cards}</div>'


@reporting_bi_web_bp.route("/reports")
def reports_home():
    kpi = KPIService.get_kpi_summary()
    revenue = ReportingService.revenue_summary()
    return f"""
    <html><head><title>DxCon Reports</title><style>{_styles()}</style></head><body>
    <div class="layout">{_sidebar("/reports")}<div class="content">
    <div class="card"><h1>Reporting Overview</h1>
    {_metric_cards([
        ("Bookings", kpi["daily_bookings"]),
        ("Orders", kpi["orders_total"]),
        ("Revenue", revenue["gross_revenue"]),
        ("Samples", kpi["samples_total"]),
        ("Results", kpi["results_total"]),
    ])}
    </div>
    <div class="card"><h2>API Endpoints</h2>
    <ul>
        <li><a href="/api/v1/reports/kpi">/api/v1/reports/kpi</a></li>
        <li><a href="/api/v1/reports/revenue">/api/v1/reports/revenue</a></li>
        <li><a href="/api/v1/reports/operations">/api/v1/reports/operations</a></li>
        <li><a href="/api/v1/reports/partners">/api/v1/reports/partners</a></li>
        <li><a href="/api/v1/reports/collectors">/api/v1/reports/collectors</a></li>
    </ul>
    </div>
    </div></div></body></html>
    """


@reporting_bi_web_bp.route("/reports/executive")
def reports_executive():
    dashboard = ExecutiveDashboardService.get_dashboard()
    kpi = dashboard["kpi"]
    revenue = dashboard["revenue"]
    partner_rows = ""
    for partner in dashboard["top_partners"]:
        partner_rows += f"""
        <tr>
            <td>{partner.get("display_name", "")}</td>
            <td>{partner.get("orders_total", 0)}</td>
            <td>{partner.get("revenue", 0)}</td>
            <td>{partner.get("completion_rate", 0)}%</td>
        </tr>
        """
    return f"""
    <html><head><title>Executive Reports</title><style>{_styles()}</style></head><body>
    <div class="layout">{_sidebar("/reports/executive")}<div class="content">
    <div class="card"><h1>Executive Dashboard</h1>
    {_metric_cards([
        ("Bookings", kpi["daily_bookings"]),
        ("Orders", kpi["orders_total"]),
        ("Gross Revenue", revenue["gross_revenue"]),
        ("SLA Compliance", f'{dashboard["sla_compliance_rate"]}%'),
    ])}
    </div>
    <div class="card"><h2>Top Partners</h2>
    <table><tr><th>Partner</th><th>Orders</th><th>Revenue</th><th>Completion</th></tr>{partner_rows}</table>
    </div>
    </div></div></body></html>
    """


@reporting_bi_web_bp.route("/reports/operations")
def reports_operations():
    ops = ReportingService.get_operations_report()
    order_status = ", ".join(f"{k}: {v}" for k, v in ops["order_status_distribution"]["by_status"].items())
    sample_status = ", ".join(f"{k}: {v}" for k, v in ops["sample_collection_status"]["by_status"].items())
    return f"""
    <html><head><title>Operations Reports</title><style>{_styles()}</style></head><body>
    <div class="layout">{_sidebar("/reports/operations")}<div class="content">
    <div class="card"><h1>Operations Dashboard</h1>
    {_metric_cards([
        ("Daily Bookings", ops["daily_bookings"]["total"]),
        ("Orders Tracked", ops["order_status_distribution"]["total"]),
        ("Samples", ops["sample_collection_status"]["total"]),
        ("SLA Compliance", f'{ops["sla_performance"]["platform_sla_compliance_rate"]}%'),
    ])}
    </div>
    <div class="card"><h2>Order Status</h2><p>{order_status or "No data"}</p></div>
    <div class="card"><h2>Sample Status</h2><p>{sample_status or "No data"}</p></div>
    <div class="card"><h2>Result Status</h2>
    <p>Test results: {ops["result_status"]["test_results_total"]} |
    Files: {ops["result_status"]["result_files_total"]}</p>
    </div>
    </div></div></body></html>
    """
