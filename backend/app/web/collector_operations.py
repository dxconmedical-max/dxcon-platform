from flask import Blueprint, redirect, request

from app.models.driver import Driver
from app.services.collector_operations import CollectorOperationsError, CollectorOperationsService


collector_operations_web_bp = Blueprint(
    "collector_operations_web",
    __name__,
)


def _page_styles():
    return """
    body { margin: 0; font-family: Arial, sans-serif; background: #f1f5f9; color: #0f172a; }
    .layout { display: flex; min-height: 100vh; }
    .sidebar { width: 240px; background: #0a4b5c; color: white; padding: 24px; }
    .sidebar h2 { margin-top: 0; margin-bottom: 30px; }
    .menu a { display: block; color: white; text-decoration: none; padding: 12px 0; border-bottom: 1px solid rgba(255,255,255,.15); }
    .content { flex: 1; padding: 32px; }
    .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; gap: 16px; flex-wrap: wrap; }
    .btn { background: #0d6efd; color: white; padding: 10px 16px; border-radius: 8px; text-decoration: none; font-weight: bold; border: none; cursor: pointer; display: inline-block; margin-right: 8px; margin-bottom: 8px; }
    .btn-secondary { background: #6c757d; }
    .card { background: white; border-radius: 12px; padding: 24px; box-shadow: 0 4px 12px rgba(0,0,0,.08); margin-bottom: 24px; }
    .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 16px; }
    .metric { background: #e0f2fe; border-radius: 12px; padding: 16px; }
    .metric strong { display: block; font-size: 28px; }
    table { width: 100%; border-collapse: collapse; background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,.08); margin-bottom: 24px; }
    th { background: #e2e8f0; text-align: left; padding: 14px; }
    td { padding: 14px; border-bottom: 1px solid #e5e7eb; vertical-align: top; }
    .badge { display: inline-block; background: #e0f2fe; color: #0369a1; padding: 4px 10px; border-radius: 999px; font-size: 12px; font-weight: bold; margin-right: 6px; }
    .alert { background: #fee2e2; color: #991b1b; padding: 12px 16px; border-radius: 8px; margin-bottom: 16px; }
    """


def _sidebar_html():
    return """
    <div class="sidebar">
        <h2>DxCon</h2>
        <div class="menu">
            <a href="/dashboard">Dashboard</a>
            <a href="/collector-operations">Collector Ops</a>
            <a href="/collector-operations/supervisor">Supervisor</a>
            <a href="/scheduling">Scheduling</a>
            <a href="/order-lifecycle">Order Lifecycle</a>
        </div>
    </div>
    """


@collector_operations_web_bp.route("/collector-operations")
def collector_operations_page():
    collectors = Driver.query.order_by(Driver.full_name.asc()).limit(20).all()
    rows = ""
    for collector in collectors:
        rows += f"""
        <tr>
            <td><a href="/collector-operations/collectors/{collector.id}">{collector.full_name}</a></td>
            <td>{collector.driver_code}</td>
            <td>{collector.phone or ""}</td>
            <td>{collector.ops_status or collector.status}</td>
            <td>{collector.vehicle_no or "-"}</td>
        </tr>
        """

    return f"""
    <html>
    <head><title>Collector Operations - DxCon</title><style>{_page_styles()}</style></head>
    <body>
        <div class="layout">
            {_sidebar_html()}
            <div class="content">
                <div class="header">
                    <h1>Collector Operations Platform</h1>
                    <a class="btn btn-secondary" href="/collector-operations/supervisor">Supervisor Dashboard</a>
                </div>
                <div class="card">
                    <p>Manage collector profiles, routes, pickups, GPS, cold boxes, and field workflow.</p>
                </div>
                <table>
                    <thead>
                        <tr>
                            <th>Collector</th>
                            <th>Code</th>
                            <th>Phone</th>
                            <th>Status</th>
                            <th>Vehicle</th>
                        </tr>
                    </thead>
                    <tbody>{rows or "<tr><td colspan='5'>No collectors found</td></tr>"}</tbody>
                </table>
            </div>
        </div>
    </body>
    </html>
    """


@collector_operations_web_bp.route("/collector-operations/collectors/<collector_id>")
def collector_dashboard_page(collector_id):
    try:
        dashboard = CollectorOperationsService.collector_dashboard(collector_id)
    except CollectorOperationsError:
        return redirect("/collector-operations")

    collector = dashboard["collector"]
    timeline_rows = ""
    for item in dashboard["recent_timeline"]:
        timeline_rows += f"""
        <tr>
            <td>{item["event_type"]}</td>
            <td>{item["message"] or ""}</td>
            <td>{item["created_at"] or ""}</td>
        </tr>
        """

    route_info = dashboard["active_route"]
    route_html = (
        f"<p><strong>Active route:</strong> {route_info['route_code']} ({route_info['status']})</p>"
        if route_info
        else "<p><strong>Active route:</strong> None</p>"
    )

    return f"""
    <html>
    <head><title>{collector["full_name"]} - Collector Dashboard</title><style>{_page_styles()}</style></head>
    <body>
        <div class="layout">
            {_sidebar_html()}
            <div class="content">
                <div class="header">
                    <h1>{collector["full_name"]}</h1>
                    <a class="btn btn-secondary" href="/collector-operations">Back</a>
                </div>
                <div class="grid">
                    <div class="metric"><strong>{dashboard["jobs_total"]}</strong>Total Jobs</div>
                    <div class="metric"><strong>{dashboard["jobs_pending"]}</strong>Pending</div>
                    <div class="metric"><strong>{dashboard["jobs_accepted"]}</strong>Accepted</div>
                    <div class="metric"><strong>{dashboard["routes_total"]}</strong>Routes</div>
                </div>
                <div class="card">
                    <p><strong>Code:</strong> {collector["driver_code"]}</p>
                    <p><strong>Phone:</strong> {collector.get("phone") or "-"}</p>
                    <p><strong>Ops status:</strong> <span class="badge">{collector.get("ops_status") or collector.get("status")}</span></p>
                    {route_html}
                </div>
                <h2>Recent Timeline</h2>
                <table>
                    <thead><tr><th>Event</th><th>Message</th><th>Time</th></tr></thead>
                    <tbody>{timeline_rows or "<tr><td colspan='3'>No timeline events</td></tr>"}</tbody>
                </table>
            </div>
        </div>
    </body>
    </html>
    """


@collector_operations_web_bp.route("/collector-operations/supervisor")
def supervisor_dashboard_page():
    dashboard = CollectorOperationsService.supervisor_dashboard()

    route_rows = ""
    for route in dashboard["recent_routes"]:
        route_rows += f"""
        <tr>
            <td>{route["route_code"]}</td>
            <td>{route["collector_id"]}</td>
            <td>{route["status"]}</td>
            <td>{route["total_stops"]}</td>
            <td>{route["total_distance_km"]}</td>
        </tr>
        """

    alert_rows = ""
    for box in dashboard["cold_box_alerts"]:
        alert_rows += f"""
        <tr>
            <td>{box["box_code"]}</td>
            <td>{box["alert_status"]}</td>
            <td>{box["temperature"]}</td>
            <td>{box["battery_level"]}</td>
        </tr>
        """

    return f"""
    <html>
    <head><title>Supervisor Dashboard - DxCon</title><style>{_page_styles()}</style></head>
    <body>
        <div class="layout">
            {_sidebar_html()}
            <div class="content">
                <div class="header">
                    <h1>Supervisor Dashboard</h1>
                    <a class="btn btn-secondary" href="/collector-operations">Collector Ops</a>
                </div>
                <div class="grid">
                    <div class="metric"><strong>{dashboard["collectors_total"]}</strong>Collectors</div>
                    <div class="metric"><strong>{dashboard["collectors_on_duty"]}</strong>On Duty</div>
                    <div class="metric"><strong>{dashboard["routes_active"]}</strong>Active Routes</div>
                    <div class="metric"><strong>{dashboard["offline_pending"]}</strong>Offline Pending</div>
                </div>
                <h2>Cold Box Alerts</h2>
                <table>
                    <thead><tr><th>Box</th><th>Alert</th><th>Temp</th><th>Battery</th></tr></thead>
                    <tbody>{alert_rows or "<tr><td colspan='4'>No alerts</td></tr>"}</tbody>
                </table>
                <h2>Recent Routes</h2>
                <table>
                    <thead><tr><th>Route</th><th>Collector</th><th>Status</th><th>Stops</th><th>Distance km</th></tr></thead>
                    <tbody>{route_rows or "<tr><td colspan='5'>No routes</td></tr>"}</tbody>
                </table>
            </div>
        </div>
    </body>
    </html>
    """
