from flask import Blueprint, request, redirect
from datetime import datetime

from app.extensions.db import db
from app.models.driver import Driver
from app.models.shipment import Shipment
from app.models.shipment_timeline import ShipmentTimeline
from app.core.audit import write_audit
from app.core.statuses import (
    SHIPMENT_ACCEPTED,
    SHIPMENT_CREATED,
)
from app.services.collector_workflow import (
    CollectorWorkflowError,
    accept_shipment,
    find_shipment,
    start_trip,
)


shipments_web_bp = Blueprint("shipments_web", __name__)


def next_shipment_code():
    count = Shipment.query.count() + 1
    return f"DXCON-SHIP-{datetime.utcnow().strftime('%Y%m%d')}-{count:04d}"


def _default_collector_id(shipment):
    if shipment.collector_id:
        return shipment.collector_id

    collector = Driver.query.first()
    return collector.id if collector else None


def _workflow_error_page(message, back_url="/shipments"):
    return f"""
    <html>
    <body style="font-family:Arial;background:#f1f5f9;padding:30px;">
        <h1>Collector Workflow Error</h1>
        <p style="color:#b91c1c;">{message}</p>
        <a href="{back_url}">Back</a>
    </body>
    </html>
    """, 400


@shipments_web_bp.route("/shipments")
def shipments_page():
    items = Shipment.query.order_by(
        Shipment.created_at.desc()
    ).all()

    rows = ""

    for s in items:
        rows += f"""
        <tr>
            <td>{s.shipment_code}</td>
            <td>{s.status}</td>
            <td>{s.lab_name or ""}</td>
            <td>{s.sample_count or 0}</td>
            <td>{s.temperature or ""}</td>
            <td>{s.received_by or ""}</td>
            <td>{s.received_at or ""}</td>
            <td>
                <a href="/shipments/{s.id}">View</a> |
                <a href="/shipments/{s.id}/qr">QR</a>
                {" | <a href='/shipments/" + s.id + "/accept'>Accept</a>" if s.status == SHIPMENT_CREATED else ""}
                {" | <a href='/shipments/" + s.id + "/start-trip'>Start Trip</a>" if s.status == SHIPMENT_ACCEPTED else ""}
                | <a href="/shipments/{s.id}/receive">Lab Receive</a>
            </td>
        </tr>
        """

    return f"""
    <html>
    <body style="font-family:Arial;background:#f1f5f9;padding:30px;">
        <h1>DxCon Shipments</h1>

        <a href="/shipments/new"
           style="background:#0d6efd;color:white;padding:10px 14px;border-radius:6px;text-decoration:none;">
           + New Shipment
        </a>

        <br><br>

        <table border="1" cellpadding="10" style="background:white;width:100%;border-collapse:collapse;">
            <tr>
                <th>Shipment</th>
                <th>Status</th>
                <th>Lab</th>
                <th>Samples</th>
                <th>Temp</th>
                <th>Received By</th>
                <th>Received At</th>
                <th>Action</th>
            </tr>
            {rows}
        </table>

        <br>
        <a href="/collector-mobile">Collector Mobile</a> |
        <a href="/monitor">Monitor</a> |
        <a href="/logistics">Logistics</a> |
        <a href="/audit">Audit</a>
    </body>
    </html>
    """


@shipments_web_bp.route("/shipments/new", methods=["GET", "POST"])
def new_shipment():
    if request.method == "POST":
        item = Shipment(
            shipment_code=request.form.get("shipment_code") or next_shipment_code(),
            collector_id=request.form.get("collector_id"),
            transport_box_id=request.form.get("transport_box_id"),
            lab_name=request.form.get("lab_name"),
            sample_count=int(request.form.get("sample_count") or 0),
            temperature=request.form.get("temperature"),
            gps_location=request.form.get("gps_location"),
            status="CREATED"
        )

        db.session.add(item)
        db.session.commit()

        write_audit(
            action="CREATE_SHIPMENT",
            object_type="SHIPMENT",
            object_id=item.id,
            user_email="WEB"
        )
        db.session.commit()

        return redirect("/shipments")

    return """
    <html>
    <body style="font-family:Arial;background:#f1f5f9;padding:30px;">
        <h1>New Shipment</h1>

        <form method="POST">
            <label>Shipment Code</label><br>
            <input name="shipment_code" placeholder="Auto if empty"><br><br>

            <label>Collector ID</label><br>
            <input name="collector_id"><br><br>

            <label>Transport Box ID</label><br>
            <input name="transport_box_id"><br><br>

            <label>Lab / Hospital Name</label><br>
            <input name="lab_name" required><br><br>

            <label>Sample Count</label><br>
            <input name="sample_count" type="number" value="0"><br><br>

            <label>Temperature</label><br>
            <input name="temperature" placeholder="4.2 C"><br><br>

            <label>GPS</label><br>
            <input name="gps_location" placeholder="10.762622,106.660172"><br><br>

            <button type="submit">Create Shipment</button>
        </form>

        <br>
        <a href="/shipments">Back</a>
    </body>
    </html>
    """


@shipments_web_bp.route("/shipments/<shipment_id>")
def shipment_detail(shipment_id):
    s = find_shipment(shipment_id)

    if not s:
        return "Shipment not found", 404

    workflow_actions = ""

    if s.status == SHIPMENT_CREATED:
        workflow_actions += f"""
        <a href="/shipments/{s.id}/accept"
           style="background:#198754;color:white;padding:10px 14px;border-radius:6px;text-decoration:none;">
           Accept Shipment
        </a>
        """

    if s.status == SHIPMENT_ACCEPTED:
        workflow_actions += f"""
        <a href="/shipments/{s.id}/start-trip"
           style="background:#f97316;color:white;padding:10px 14px;border-radius:6px;text-decoration:none;">
           Start Trip
        </a>
        """

    timeline_items = ShipmentTimeline.query.filter_by(
        shipment_id=s.id
    ).order_by(
        ShipmentTimeline.created_at.asc()
    ).all()

    timeline_rows = ""

    for item in timeline_items:
        timeline_rows += f"""
        <tr>
            <td>{item.created_at}</td>
            <td>{item.event_type}</td>
            <td>{item.actor or ""}</td>
            <td>{item.gps_location or ""}</td>
            <td>{item.note or ""}</td>
        </tr>
        """

    if not timeline_rows:
        timeline_rows = """
        <tr>
            <td colspan="5">No timeline events yet.</td>
        </tr>
        """

    return f"""
    <html>
    <body style="font-family:Arial;background:#f1f5f9;padding:30px;">
        <h1>Shipment Detail</h1>

        <div style="background:white;padding:20px;border-radius:12px;">
            <p><b>Code:</b> {s.shipment_code}</p>
            <p><b>Status:</b> {s.status}</p>
            <p><b>Collector:</b> {s.collector_id or ""}</p>
            <p><b>Transport Box:</b> {s.transport_box_id or ""}</p>
            <p><b>Lab:</b> {s.lab_name}</p>
            <p><b>Samples:</b> {s.sample_count}</p>
            <p><b>Temperature:</b> {s.temperature}</p>
            <p><b>GPS:</b> {s.gps_location or ""}</p>
            <p><b>Departed At:</b> {s.departed_at or ""}</p>
            <p><b>QR:</b> {s.qr_payload()}</p>
            <p><b>Received By:</b> {s.received_by or ""}</p>
            <p><b>Received At:</b> {s.received_at or ""}</p>
            <p><b>Note:</b> {s.receiver_note or ""}</p>
        </div>

        <br>
        {workflow_actions}
        {"<br><br>" if workflow_actions else ""}
        <a href="/shipments/{s.id}/qr">Show QR</a> |
        <a href="/shipments/{s.id}/receive">Lab Receive</a> |
        <a href="/shipments">Back</a>

        <br><br>

        <div style="background:white;padding:20px;border-radius:12px;">
            <h2>Shipment Timeline</h2>
            <table border="1" cellpadding="8" style="width:100%;border-collapse:collapse;">
                <tr>
                    <th>Time</th>
                    <th>Event</th>
                    <th>Actor</th>
                    <th>GPS</th>
                    <th>Note</th>
                </tr>
                {timeline_rows}
            </table>
        </div>
    </body>
    </html>
    """


@shipments_web_bp.route("/shipments/<shipment_id>/accept", methods=["GET", "POST"])
def accept_shipment_web(shipment_id):
    s = find_shipment(shipment_id)

    if not s:
        return "Shipment not found", 404

    try:
        accept_shipment(
            s,
            collector_id=_default_collector_id(s),
            actor="WEB",
        )
    except CollectorWorkflowError as exc:
        return _workflow_error_page(exc.message, f"/shipments/{s.id}")

    return redirect(f"/shipments/{s.id}")


@shipments_web_bp.route("/shipments/<shipment_id>/start-trip", methods=["GET", "POST"])
def start_trip_web(shipment_id):
    s = find_shipment(shipment_id)

    if not s:
        return "Shipment not found", 404

    try:
        start_trip(
            s,
            collector_id=_default_collector_id(s),
            actor="WEB",
        )
    except CollectorWorkflowError as exc:
        return _workflow_error_page(exc.message, f"/shipments/{s.id}")

    return redirect(f"/shipments/{s.id}")


@shipments_web_bp.route("/shipments/<shipment_id>/qr")
def shipment_qr(shipment_id):
    s = Shipment.query.get(shipment_id)

    if not s:
        return "Shipment not found", 404

    return f"""
    <html>
    <body style="font-family:Arial;background:#f1f5f9;padding:30px;text-align:center;">
        <h1>Shipment QR</h1>
        <h2>{s.shipment_code}</h2>

        <div style="font-size:24px;background:white;padding:30px;border-radius:12px;display:inline-block;border:2px dashed #0d6efd;">
            {s.qr_payload()}
        </div>

        <p>Lab app sẽ scan payload này để xác nhận nhận mẫu.</p>

        <br>
        <a href="/shipments/{s.id}/receive">Simulate Lab Receive</a> |
        <a href="/shipments">Back</a>
    </body>
    </html>
    """


@shipments_web_bp.route("/shipments/<shipment_id>/receive", methods=["GET", "POST"])
def lab_receive(shipment_id):
    s = Shipment.query.get(shipment_id)

    if not s:
        return "Shipment not found", 404

    if request.method == "POST":
        s.status = "RECEIVED"
        s.received_at = datetime.utcnow()
        s.received_by = request.form.get("received_by") or "LAB"
        s.receiver_note = request.form.get("receiver_note")

        write_audit(
            action="LAB_RECEIVED_SHIPMENT",
            object_type="SHIPMENT",
            object_id=s.id,
            user_email=s.received_by
        )

        db.session.commit()

        return redirect(f"/shipments/{s.id}")

    return f"""
    <html>
    <body style="font-family:Arial;background:#f1f5f9;padding:30px;">
        <h1>Lab Receive Confirmation</h1>

        <div style="background:white;padding:20px;border-radius:12px;">
            <p><b>Shipment:</b> {s.shipment_code}</p>
            <p><b>Status:</b> {s.status}</p>
            <p><b>Lab:</b> {s.lab_name}</p>
            <p><b>Samples:</b> {s.sample_count}</p>
            <p><b>Temperature:</b> {s.temperature}</p>
            <p><b>QR Payload:</b> {s.qr_payload()}</p>
        </div>

        <br>

        <form method="POST">
            <label>Received By</label><br>
            <input name="received_by" placeholder="Lab staff name"><br><br>

            <label>Note</label><br>
            <textarea name="receiver_note" rows="4" cols="60"></textarea><br><br>

            <button type="submit"
                style="background:#198754;color:white;padding:12px 18px;border:0;border-radius:6px;">
                CONFIRM RECEIVED
            </button>
        </form>

        <br>
        <a href="/shipments">Back</a>
    </body>
    </html>
    """
