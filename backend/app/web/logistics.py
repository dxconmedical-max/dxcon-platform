from flask import Blueprint

from app.extensions.db import db
from app.infrastructure.schema_introspection import table_exists_name
from app.models.order import Order
from app.models.home_collection import HomeCollection
from app.models.driver import Driver
from app.models.transport_box import TransportBox
from app.models.sample_collection import SampleCollection
from app.models.sample_event import SampleEvent
from app.models.sample_tracking import SampleTracking
from app.models.shipment import Shipment
from app.web.demo_pilot_lib import (
    DEMO_ORDER_PREFIX,
    metric_cards,
    render_pilot_page,
    safe_query,
    seeded_summary,
)


logistics_web_bp = Blueprint("logistics_web", __name__)


def color(status):
    return {
        "CHECKED_IN": "#198754",
        "IN_TRANSIT": "#f97316",
        "RECEIVED": "#7c3aed",
        "PROCESSING": "#0d6efd",
        "COMPLETED": "#198754",
        "COLLECTED": "#f97316",
        "PENDING": "#64748b",
        "REQUESTED": "#64748b",
    }.get(status or "", "#0d6efd")


@logistics_web_bp.route("/logistics")
def logistics_dashboard():
    summary = seeded_summary()
    notice = ""
    rows = ""

    if table_exists_name("sample_trackings"):
        try:
            samples = SampleTracking.query.order_by(SampleTracking.updated_at.desc()).limit(20).all()
            for s in samples:
                rows += f"""
                <tr>
                    <td>{s.sample_code}</td>
                    <td><b style="color:{color(s.status)}">{s.status}</b></td>
                    <td>{s.collector_id or ""}</td>
                    <td>{s.transport_box_id or ""}</td>
                    <td><a href="{s.map_url() or '#'}" target="_blank">Map</a></td>
                    <td>{s.updated_at}</td>
                </tr>
                """
        except Exception:
            rows = ""

    if not rows and table_exists_name("sample_collections"):
        notice = """
        <div class="notice">
            Sample tracking is unavailable. Showing seeded sample collections and shipments instead.
        </div>
        """
        collections = safe_query(SampleCollection, limit=20)
        shipments = safe_query(Shipment, filter_like=("shipment_code", "DEMO-SHP-"), limit=20) if table_exists_name("shipments") else []
        for item in collections:
            rows += f"<tr><td>{item.order_id}</td><td>{item.status}</td><td>{item.collector_name or ''}</td><td>collection</td><td>-</td><td>{item.created_at or ''}</td></tr>"
        for item in shipments:
            rows += f"<tr><td>{item.shipment_code}</td><td>{item.status}</td><td>{item.collector_id or ''}</td><td>shipment</td><td>-</td><td>{item.created_at or ''}</td></tr>"

    if not rows:
        notice = """
        <div class="notice">
            Logistics tracking tables are empty or unavailable. Showing demo order logistics status instead.
        </div>
        """
        orders = safe_query(Order, filter_like=("order_code", DEMO_ORDER_PREFIX), limit=20)
        for order in orders:
            rows += f"<tr><td>{order.order_code}</td><td>{order.status}</td><td>{order.patient_id}</td><td>order</td><td>-</td><td>{order.created_at or ''}</td></tr>"

    if not rows:
        rows = "<tr><td colspan='6'>No logistics or demo order data found.</td></tr>"

    event_rows = ""
    if table_exists_name("sample_events"):
        try:
            events = SampleEvent.query.order_by(SampleEvent.created_at.desc()).limit(15).all()
            for e in events:
                event_rows += f"""
                <div style="border-left:6px solid {color(e.event_type)};background:white;padding:14px;margin-bottom:10px;border-radius:8px;">
                    <b>{e.event_type}</b><br>{e.note or ""}<br><small>{e.created_at}</small>
                </div>
                """
        except Exception:
            event_rows = ""

    if not event_rows:
        event_rows = "<p>No timeline events available. Demo orders and collections are listed above.</p>"

    body = f"""
    <h1>Logistics Dashboard</h1>
    <p style="color:#475569;">Sample movement, collections, shipments, or order status fallback.</p>
    {notice}
    {metric_cards([
        ("Demo Orders", summary["orders"]),
        ("Demo Patients", summary["patients"]),
        ("Demo Tests", summary["test_catalog"]),
        ("Demo Users", summary["users"]),
    ])}
    <div class="card">
        <h2>Live Logistics View</h2>
        <table><tr><th>Reference</th><th>Status</th><th>Actor</th><th>Type</th><th>Link</th><th>Updated</th></tr>{rows}</table>
    </div>
    <div class="card"><h2>Operations Timeline</h2>{event_rows}</div>
    <div class="card"><p><a href="/logistics/dispatch">Dispatch Center</a> · <a href="/shipments">Shipments</a> · <a href="/collector">Collector Portal</a></p></div>
    """
    return render_pilot_page("Logistics Dashboard", body)


@logistics_web_bp.route("/logistics/dispatch")
def dispatch_center():

    jobs = HomeCollection.query.all()
    collectors = Driver.query.all()

    job_rows = ""

    for job in jobs:
        assign_links = ""

        for c in collectors:
            assign_links += f"""
            <a href="/logistics/dispatch/assign/{job.id}/{c.id}">
                Assign {c.driver_code}
            </a><br>
            """

        job_rows += f"""
        <tr>
            <td>{job.id}</td>
            <td>{job.address}</td>
            <td>{job.scheduled_time}</td>
            <td>{job.status}</td>
            <td>{job.collector_id or ""}</td>
            <td>{assign_links}</td>
        </tr>
        """

    collector_rows = ""

    for c in collectors:
        collector_rows += f"""
        <tr>
            <td>{c.driver_code}</td>
            <td>{c.full_name}</td>
            <td>{c.phone or ""}</td>
            <td>{c.vehicle_no or ""}</td>
            <td>{c.status}</td>
        </tr>
        """

    return f"""
    <html>
    <body style="font-family:Arial;background:#f1f5f9;padding:30px;">
        <h1>DxCon Dispatch Center V6</h1>

        <h2>Collection Jobs</h2>
        <table border="1" cellpadding="10" style="background:white;width:100%;border-collapse:collapse;">
            <tr>
                <th>Job ID</th>
                <th>Address</th>
                <th>Schedule</th>
                <th>Status</th>
                <th>Collector</th>
                <th>Assign</th>
            </tr>
            {job_rows}
        </table>

        <h2>Collectors</h2>
        <table border="1" cellpadding="10" style="background:white;width:100%;border-collapse:collapse;">
            <tr>
                <th>Code</th>
                <th>Name</th>
                <th>Phone</th>
                <th>Vehicle</th>
                <th>Status</th>
            </tr>
            {collector_rows}
        </table>

        <br>
        <a href="/logistics">Back Logistics</a> |
        <a href="/logistics/routes">Route Planner</a> |
        <a href="/logistics/live-map">Live Map</a>
    </body>
    </html>
    """


@logistics_web_bp.route("/logistics/dispatch/assign/<job_id>/<collector_id>")
def assign_collector(job_id, collector_id):

    job = HomeCollection.query.get(job_id)

    if not job:
        return "Job not found"

    job.collector_id = collector_id
    job.status = "ASSIGNED"

    db.session.commit()

    return """
    <h2>Collector assigned</h2>
    <a href="/logistics/dispatch">Back Dispatch</a>
    """


@logistics_web_bp.route("/iot-box")
def iot_box_dashboard():

    boxes = TransportBox.query.all()

    rows = ""

    for b in boxes:
        b.update_alert_status()
        db.session.commit()

        rows += f"""
        <tr>
            <td>{b.box_code}</td>
            <td>{b.driver_id or ""}</td>
            <td>{b.temperature}</td>
            <td>{b.battery_level}%</td>
            <td><b style="color:{'#dc3545' if b.alert_status != 'NORMAL' else '#198754'}">{b.alert_status}</b></td>
            <td>{b.status}</td>
            <td><a href="{b.map_url() or '#'}" target="_blank">Map</a></td>
            <td>
                <a href="/iot-box/simulate-temp-high/{b.id}">Temp High</a><br>
                <a href="/iot-box/simulate-normal/{b.id}">Normal</a>
            </td>
        </tr>
        """

    return f"""
    <html>
    <body style="font-family:Arial;background:#f1f5f9;padding:30px;">
        <h1>DxCon IoT Transport Box V7</h1>

        <p>
            <a href="/iot-box/create-demo">Create Demo Box</a>
        </p>

        <table border="1" cellpadding="10" style="background:white;width:100%;border-collapse:collapse;">
            <tr>
                <th>Box</th>
                <th>Driver</th>
                <th>Temperature</th>
                <th>Battery</th>
                <th>Alert</th>
                <th>Status</th>
                <th>GPS</th>
                <th>Actions</th>
            </tr>
            {rows}
        </table>

        <br>
        <a href="/logistics">Back Logistics</a> |
        <a href="/logistics/routes">Route Planner</a> |
        <a href="/logistics/live-map">Live Map</a>
    </body>
    </html>
    """


@logistics_web_bp.route("/iot-box/create-demo")
def create_demo_box():

    code = "BOX-DEMO-001"

    box = TransportBox.query.filter_by(
        box_code=code
    ).first()

    if not box:
        box = TransportBox(
            box_code=code,
            temperature=4.0,
            battery_level=98,
            latitude="10.0452",
            longitude="105.7469",
            status="ONLINE",
            alert_status="NORMAL"
        )

        db.session.add(box)
        db.session.commit()

    return """
    <h2>Demo box ready</h2>
    <a href="/iot-box">Back IoT Box</a>
    """


@logistics_web_bp.route("/iot-box/simulate-temp-high/<box_id>")
def simulate_temp_high(box_id):

    box = TransportBox.query.get(box_id)

    if not box:
        return "Box not found"

    box.temperature = 12.5
    box.battery_level = 72
    box.update_alert_status()

    db.session.commit()

    return """
    <h2>Temperature alert simulated</h2>
    <a href="/iot-box">Back IoT Box</a>
    """


@logistics_web_bp.route("/iot-box/simulate-normal/<box_id>")
def simulate_normal(box_id):

    box = TransportBox.query.get(box_id)

    if not box:
        return "Box not found"

    box.temperature = 4.0
    box.battery_level = 96
    box.update_alert_status()

    db.session.commit()

    return """
    <h2>Box normalized</h2>
    <a href="/iot-box">Back IoT Box</a>
    """


@logistics_web_bp.route("/logistics/routes")
def logistics_routes_page():
    from app.models.logistics_route import RoutePlan, RouteStop

    routes = RoutePlan.query.order_by(RoutePlan.created_at.desc()).limit(30).all()
    rows = ""
    for route in routes:
        stop_count = RouteStop.query.filter_by(route_plan_id=route.id).count()
        rows += f"""
        <tr>
            <td>{route.route_code}</td>
            <td>{route.status}</td>
            <td>{stop_count}</td>
            <td>{route.total_distance_km}</td>
            <td>{route.estimated_minutes}</td>
            <td>{route.optimized_at or ""}</td>
        </tr>
        """

    return f"""
    <html>
    <body style="font-family:Arial;background:#f1f5f9;padding:30px;">
        <h1>Logistics Route Planner</h1>
        <table border="1" cellpadding="10" style="background:white;width:100%;border-collapse:collapse;">
            <tr>
                <th>Route</th>
                <th>Status</th>
                <th>Stops</th>
                <th>Distance (km)</th>
                <th>ETA (min)</th>
                <th>Optimized</th>
            </tr>
            {rows}
        </table>
        <br>
        <a href="/logistics">Back Logistics</a> |
        <a href="/logistics/dispatch">Dispatch</a> |
        <a href="/logistics/live-map">Live Map</a>
    </body>
    </html>
    """


@logistics_web_bp.route("/logistics/live-map")
def logistics_live_map():
    from app.models.logistics_tracking import GPSPing
    from app.models.logistics_driver import Vehicle

    pings = GPSPing.query.order_by(GPSPing.recorded_at.desc()).limit(50).all()
    vehicles = Vehicle.query.all()
    ping_rows = ""
    for ping in pings:
        ping_rows += f"""
        <tr>
            <td>{ping.recorded_at}</td>
            <td>{ping.latitude}</td>
            <td>{ping.longitude}</td>
            <td>{ping.speed}</td>
            <td>{ping.driver_profile_id or ""}</td>
        </tr>
        """
    vehicle_rows = ""
    for vehicle in vehicles:
        vehicle_rows += f"""
        <tr>
            <td>{vehicle.vehicle_code}</td>
            <td>{vehicle.plate_number}</td>
            <td>{vehicle.status}</td>
            <td>{vehicle.latitude or ""}</td>
            <td>{vehicle.longitude or ""}</td>
        </tr>
        """

    return f"""
    <html>
    <body style="font-family:Arial;background:#f1f5f9;padding:30px;">
        <h1>Logistics Live Map</h1>
        <h2>Recent GPS Pings</h2>
        <table border="1" cellpadding="10" style="background:white;width:100%;border-collapse:collapse;">
            <tr><th>Time</th><th>Lat</th><th>Lng</th><th>Speed</th><th>Driver</th></tr>
            {ping_rows}
        </table>
        <h2>Vehicles</h2>
        <table border="1" cellpadding="10" style="background:white;width:100%;border-collapse:collapse;">
            <tr><th>Code</th><th>Plate</th><th>Status</th><th>Lat</th><th>Lng</th></tr>
            {vehicle_rows}
        </table>
        <br>
        <a href="/logistics">Back Logistics</a> |
        <a href="/logistics/routes">Routes</a> |
        <a href="/logistics/dispatch">Dispatch</a>
    </body>
    </html>
    """
