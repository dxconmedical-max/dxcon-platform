from flask import Blueprint
from app.models.shipment import Shipment
from app.models.shipment_item import ShipmentItem
from app.models.shipment_timeline import ShipmentTimeline
from app.models.event_log import EventLog


logistics_v2_web_bp = Blueprint(
    "logistics_v2_web",
    __name__
)


@logistics_v2_web_bp.route("/logistics-v2")
def logistics_v2_dashboard():
    shipment_count = Shipment.query.count()
    item_count = ShipmentItem.query.count()
    event_count = EventLog.query.count()

    waiting_receive = Shipment.query.filter(
        Shipment.status.in_(["IN_TRANSIT", "ARRIVED"])
    ).count()

    received = Shipment.query.filter_by(
        status="RECEIVED"
    ).count()

    recent_events = EventLog.query.order_by(
        EventLog.created_at.desc()
    ).limit(20).all()

    event_rows = ""

    for e in recent_events:
        event_rows += f"""
        <tr>
            <td>{e.created_at}</td>
            <td>{e.event_type}</td>
            <td>{e.object_type or ""}</td>
            <td>{e.message or ""}</td>
            <td>{e.severity}</td>
        </tr>
        """

    return f"""
    <html>
    <body style="font-family:Arial;background:#f1f5f9;padding:30px;">
        <h1>DxCon Logistics V2</h1>

        <div style="display:flex;gap:15px;flex-wrap:wrap;">
            <div class="card"><h3>Shipments</h3><h1>{shipment_count}</h1></div>
            <div class="card"><h3>Items</h3><h1>{item_count}</h1></div>
            <div class="card"><h3>Waiting Receive</h3><h1>{waiting_receive}</h1></div>
            <div class="card"><h3>Received</h3><h1>{received}</h1></div>
            <div class="card"><h3>Events</h3><h1>{event_count}</h1></div>
        </div>

        <br>

        <div style="background:white;padding:20px;border-radius:12px;">
            <h2>Recent Logistics Events</h2>
            <table border="1" cellpadding="8" style="width:100%;border-collapse:collapse;">
                <tr>
                    <th>Time</th>
                    <th>Event</th>
                    <th>Object</th>
                    <th>Message</th>
                    <th>Severity</th>
                </tr>
                {event_rows}
            </table>
        </div>

        <br>
        <a href="/shipments">Shipments</a> |
        <a href="/monitor">Monitor</a> |
        <a href="/audit">Audit</a>

        <style>
            .card {{
                background:white;
                padding:20px;
                border-radius:12px;
                width:190px;
                box-shadow:0 4px 12px rgba(0,0,0,.08);
            }}
        </style>
    </body>
    </html>
    """
