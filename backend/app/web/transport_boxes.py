from flask import Blueprint, request, redirect

from app.extensions.db import db
from app.models.transport_box import TransportBox
from app.models.driver import Driver
from app.models.sample_tracking import SampleTracking
from app.models.home_collection import HomeCollection
from app.models.patient import Patient
from app.utils.auth import role_required


transport_boxes_web_bp = Blueprint(
    "transport_boxes_web",
    __name__
)


@transport_boxes_web_bp.route("/transport-boxes")
@role_required("SUPER_ADMIN", "LAB_TECHNICIAN", "COLLECTOR")
def transport_boxes_page():

    boxes = TransportBox.query.all()

    rows = ""

    for box in boxes:

        alert_color = "#198754"

        if box.alert_status != "NORMAL":
            alert_color = "#dc3545"

        map_link = ""

        if box.latitude and box.longitude:
            map_link = f"""
            <a target="_blank" href="{box.map_url()}">
                View Map
            </a>
            """

        rows += f"""
        <tr>
            <td>{box.box_code}</td>
            <td>{box.temperature} °C</td>
            <td>{Driver.query.get(box.driver_id).full_name if box.driver_id and Driver.query.get(box.driver_id) else ""}</td>
            <td>{box.battery_level}%</td>
            <td>{box.status}</td>
            <td style="color:{alert_color};font-weight:bold;">
                {box.alert_status}
            </td>
            <td>{box.latitude or ""}</td>
            <td>{box.longitude or ""}</td>
            <td>{map_link}</td>
            <td>
                <a href="/transport-boxes/{box.id}/samples">Samples</a> | <a href="/transport-boxes/update/{box.id}">
                    Update
                </a>
            </td>
        </tr>
        """

    return f"""
    <html>
    <body style="font-family:Arial;background:#f1f5f9;padding:30px;">

        <h1>Transport Boxes IoT</h1>

        <a href="/transport-boxes/new"
           style="background:#0d6efd;color:white;padding:10px 15px;text-decoration:none;border-radius:6px;">
           + New Box
        </a>

        <br><br>

        <table border="1" cellpadding="10" style="background:white;width:100%;">
            <tr>
                <th>Box Code</th>
                <th>Temperature</th>
                <th>Driver</th>
                <th>Battery</th>
                <th>Status</th>
                <th>Alert</th>
                <th>Latitude</th>
                <th>Longitude</th>
                <th>Map</th>
                <th>Action</th>
            </tr>

            {rows}

        </table>

        <br>
        <a href="/dashboard">Back to Dashboard</a>

    </body>
    </html>
    """


@transport_boxes_web_bp.route("/transport-boxes/new", methods=["GET", "POST"])
@role_required("SUPER_ADMIN", "LAB_TECHNICIAN")
def new_transport_box():

    if request.method == "POST":

        box = TransportBox(
            box_code=request.form.get("box_code"),
            temperature=float(request.form.get("temperature") or 4.0),
            battery_level=int(request.form.get("battery_level") or 100),
            latitude=request.form.get("latitude"),
            longitude=request.form.get("longitude"),
            status=request.form.get("status") or "ONLINE"
        )

        box.update_alert_status()

        db.session.add(box)
        db.session.commit()

        return redirect("/transport-boxes")

    return """
    <html>
    <body style="font-family:Arial;background:#f1f5f9;padding:30px;">

        <h1>New Transport Box</h1>

        <form method="POST">

            <label>Box Code</label><br>
            <input name="box_code" placeholder="BOX001" required>

            <br><br>

            <label>Temperature</label><br>
            <input name="temperature" placeholder="4.0">

            <br><br>

            <label>Battery Level</label><br>
            <input name="battery_level" placeholder="100">

            <br><br>

            <label>Latitude</label><br>
            <input name="latitude" placeholder="10.7769">

            <br><br>

            <label>Longitude</label><br>
            <input name="longitude" placeholder="106.7009">

            <br><br>

            <label>Status</label><br>
            <select name="status">
                <option value="ONLINE">ONLINE</option>
                <option value="OFFLINE">OFFLINE</option>
                <option value="IN_USE">IN_USE</option>
                <option value="MAINTENANCE">MAINTENANCE</option>
            </select>

            <br><br>

            <button type="submit">
                Save Box
            </button>

        </form>

        <br>
        <a href="/transport-boxes">Back</a>

    </body>
    </html>
    """


@transport_boxes_web_bp.route("/transport-boxes/update/<box_id>", methods=["GET", "POST"])
@role_required("SUPER_ADMIN", "LAB_TECHNICIAN", "COLLECTOR")
def update_transport_box_web(box_id):

    box = TransportBox.query.get(box_id)

    if not box:
        return "Transport box not found"

    if request.method == "POST":

        box.temperature = float(request.form.get("temperature") or box.temperature or 4.0)
        box.battery_level = int(request.form.get("battery_level") or box.battery_level or 100)
        box.latitude = request.form.get("latitude")
        box.longitude = request.form.get("longitude")
        box.status = request.form.get("status") or box.status
        box.driver_id = request.form.get("driver_id") or box.driver_id

        box.update_alert_status()

        db.session.commit()

        return redirect("/transport-boxes")

    drivers = Driver.query.all()

    driver_options = ""

    for driver in drivers:
        selected = "selected" if box.driver_id == driver.id else ""
        driver_options += f"""
        <option value="{driver.id}" {selected}>
            {driver.driver_code} - {driver.full_name}
        </option>
        """

    return f"""
    <html>
    <body style="font-family:Arial;background:#f1f5f9;padding:30px;">

        <h1>Update Transport Box - {box.box_code}</h1>

        <form method="POST">

            <label>Driver</label><br>
            <select name="driver_id">
                <option value="">No Driver</option>
                {driver_options}
            </select>

            <br><br>

            <label>Temperature</label><br>
            <input name="temperature" value="{box.temperature}">

            <br><br>

            <label>Battery Level</label><br>
            <input name="battery_level" value="{box.battery_level}">

            <br><br>

            <label>Latitude</label><br>
            <input name="latitude" value="{box.latitude or ""}">

            <br><br>

            <label>Longitude</label><br>
            <input name="longitude" value="{box.longitude or ""}">

            <br><br>

            <label>Status</label><br>
            <select name="status">
                <option value="ONLINE">ONLINE</option>
                <option value="OFFLINE">OFFLINE</option>
                <option value="IN_USE">IN_USE</option>
                <option value="MAINTENANCE">MAINTENANCE</option>
            </select>

            <br><br>

            <button type="submit">
                Update Box
            </button>

        </form>

        <br>
        <a href="/transport-boxes">Back</a>

    </body>
    </html>
    """


@transport_boxes_web_bp.route("/transport-boxes/<box_id>/samples")
@role_required("SUPER_ADMIN", "LAB_TECHNICIAN", "COLLECTOR")
def transport_box_samples(box_id):

    box = TransportBox.query.get(box_id)

    if not box:
        return "Transport box not found"

    samples = SampleTracking.query.filter_by(
        transport_box_id=box.id
    ).all()

    rows = ""

    for sample in samples:

        patient_name = ""

        if sample.home_collection_id:
            collection = HomeCollection.query.get(sample.home_collection_id)

            if collection:
                patient = Patient.query.get(collection.patient_id)
                patient_name = patient.full_name if patient else ""

        rows += f"""
        <tr>
            <td>{sample.sample_code}</td>
            <td>{patient_name}</td>
            <td>{sample.status}</td>
            <td>
                <a href="/samples/verify/{sample.sample_code}">
                    Verify
                </a>
            </td>
        </tr>
        """

    return f"""
    <html>
    <body style="font-family:Arial;background:#f1f5f9;padding:30px;">

        <h1>Samples in Box - {box.box_code}</h1>

        <p><strong>Temperature:</strong> {box.temperature} °C</p>
        <p><strong>Battery:</strong> {box.battery_level}%</p>
        <p><strong>Alert:</strong> {box.alert_status}</p>

        <table border="1" cellpadding="10" style="background:white;width:100%;">
            <tr>
                <th>Sample Code</th>
                <th>Patient</th>
                <th>Status</th>
                <th>Action</th>
            </tr>
            {rows}
        </table>

        <br>
        <a href="/transport-boxes">Back to Transport Boxes</a>

    </body>
    </html>
    """
