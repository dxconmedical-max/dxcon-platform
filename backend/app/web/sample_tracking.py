from flask import Blueprint, request, redirect, session

from app.extensions.db import db
from app.models.sample_tracking import SampleTracking
from app.models.home_collection import HomeCollection
from app.models.patient import Patient
from app.models.sample_event import SampleEvent
from app.models.transport_box import TransportBox
from app.utils.auth import role_required

import uuid


sample_tracking_web_bp = Blueprint("sample_tracking_web", __name__)


def generate_sample_code():
    return "DX-SAMPLE-" + str(uuid.uuid4())[:8].upper()


def qr_url(sample_code):
    return (
        "https://api.qrserver.com/v1/create-qr-code/"
        f"?size=120x120&data={sample_code}"
    )


def map_url(latitude, longitude):
    if latitude and longitude:
        return f"https://maps.google.com/?q={latitude},{longitude}"
    return ""


@sample_tracking_web_bp.route("/samples")
@role_required("SUPER_ADMIN", "LAB_TECHNICIAN", "COLLECTOR")
def samples_page():

    samples = SampleTracking.query.all()
    rows = ""

    for sample in samples:

        collection = None
        patient_name = ""

        if sample.home_collection_id:
            collection = HomeCollection.query.get(sample.home_collection_id)

        if collection:
            patient = Patient.query.get(collection.patient_id)
            patient_name = patient.full_name if patient else ""

        box_info = ""

        if sample.transport_box_id:
            box = TransportBox.query.get(sample.transport_box_id)

            if box:
                box_info = f"{box.box_code} - {box.temperature} °C - {box.alert_status}"

        gps_link = ""

        if sample.latitude and sample.longitude:
            gps_link = f"""
            <a target="_blank" href="{map_url(sample.latitude, sample.longitude)}">
                View Map
            </a>
            """

        rows += f"""
        <tr>
            <td>
                <strong>{sample.sample_code}</strong><br>
                <img src="{qr_url(sample.sample_code)}">
            </td>
            <td>{patient_name}</td>
            <td>{box_info}</td>
            <td>{sample.status}</td>
            <td>{sample.latitude or ""}</td>
            <td>{sample.longitude or ""}</td>
            <td>{gps_link}</td>
            <td>
                <a href="/samples/verify/{sample.sample_code}">Verify</a>
                |
                <a href="/samples/status/{sample.id}/COLLECTED">Collected</a>
                |
                <a href="/samples/status/{sample.id}/IN_TRANSIT">In Transit</a>
                |
                <a href="/samples/status/{sample.id}/RECEIVED">Received</a>
                |
                <a href="/samples/status/{sample.id}/PROCESSING">Processing</a>
                |
                <a href="/samples/status/{sample.id}/COMPLETED">Completed</a>
            </td>
        </tr>
        """

    return f"""
    <html>
    <body style="font-family:Arial;background:#f1f5f9;padding:30px;">

        <h1>Sample Tracking</h1>

        <a href="/samples/new"
           style="background:#0d6efd;color:white;padding:10px 15px;text-decoration:none;border-radius:6px;">
           + New Sample Check-in
        </a>

        <br><br>

        <table border="1" cellpadding="10" style="background:white;width:100%;">
            <tr>
                <th>Sample / QR</th>
                <th>Patient</th>
                <th>Transport Box</th>
                <th>Status</th>
                <th>Latitude</th>
                <th>Longitude</th>
                <th>GPS</th>
                <th>Action</th>
            </tr>
            {rows}
        </table>

        <br>
        <a href="/dashboard">Back to Dashboard</a>

    </body>
    </html>
    """


@sample_tracking_web_bp.route("/samples/new", methods=["GET", "POST"])
@role_required("SUPER_ADMIN", "COLLECTOR")
def new_sample():

    collections = HomeCollection.query.all()
    boxes = TransportBox.query.all()

    if request.method == "POST":

        item = SampleTracking(
            sample_code=generate_sample_code(),
            home_collection_id=request.form.get("home_collection_id"),
            collector_id=session.get("user_id"),
            transport_box_id=request.form.get("transport_box_id"),
            latitude=request.form.get("latitude"),
            longitude=request.form.get("longitude"),
            status="CHECKED_IN"
        )

        db.session.add(item)
        db.session.commit()

        return redirect("/samples")

    collection_options = ""

    for collection in collections:

        patient = Patient.query.get(collection.patient_id)
        patient_name = patient.full_name if patient else ""

        collection_options += f"""
        <option value="{collection.id}">
            {patient_name} - {collection.address} - {collection.status}
        </option>
        """

    box_options = ""

    for box in boxes:
        box_options += f"""
        <option value="{box.id}">
            {box.box_code} - {box.temperature} °C - {box.alert_status}
        </option>
        """

    box_options = ""

    for box in boxes:
        box_options += f"""
        <option value="{box.id}">
            {box.box_code} - {box.temperature} °C - {box.alert_status}
        </option>
        """

    return f"""
    <html>
    <body style="font-family:Arial;background:#f1f5f9;padding:30px;">

        <h1>New Sample Check-in</h1>

        <form method="POST">

            <label>Home Collection</label><br>
            <select name="home_collection_id">
                {collection_options}
            </select>

            <br><br>

            <label>Transport Box</label><br>
            <select name="transport_box_id">
                {box_options}
            </select>

            <br><br>

            <label>Latitude</label><br>
            <input name="latitude" placeholder="10.7769">

            <br><br>

            <label>Longitude</label><br>
            <input name="longitude" placeholder="106.7009">

            <br><br>

            <button type="submit">Check-in Sample</button>

        </form>

        <br>
        <a href="/samples">Back to Samples</a>

    </body>
    </html>
    """


@sample_tracking_web_bp.route("/samples/status/<sample_id>/<status>")
@role_required("SUPER_ADMIN", "LAB_TECHNICIAN", "COLLECTOR")
def update_sample_status_web(sample_id, status):

    sample = SampleTracking.query.get(sample_id)

    if not sample:
        return "Sample not found"

    sample.status = status

    event = SampleEvent(
        sample_tracking_id=sample.id,
        event_type=status,
        note=f"Sample status changed to {status}"
    )

    db.session.add(event)
    db.session.commit()

    return redirect("/samples")


@sample_tracking_web_bp.route("/samples/verify/<sample_code>")
def verify_sample(sample_code):

    sample = SampleTracking.query.filter_by(sample_code=sample_code).first()

    if not sample:
        return """
        <h2>Sample not found</h2>
        <a href="/samples">Back</a>
        """

    patient_name = ""

    if sample.home_collection_id:
        collection = HomeCollection.query.get(sample.home_collection_id)

        if collection:
            patient = Patient.query.get(collection.patient_id)
            patient_name = patient.full_name if patient else ""

    box_info = ""

    if sample.transport_box_id:
        box = TransportBox.query.get(sample.transport_box_id)

        if box:
            box_info = f"{box.box_code} - {box.temperature} °C - {box.alert_status}"

    gps_link = ""

    if sample.latitude and sample.longitude:
        gps_link = f"""
        <a target="_blank" href="{map_url(sample.latitude, sample.longitude)}">
            View Collector Location
        </a>
        """

    events = SampleEvent.query.filter_by(
        sample_tracking_id=sample.id
    ).order_by(SampleEvent.created_at.asc()).all()

    event_rows = ""

    for event in events:
        event_rows += f"""
        <tr>
            <td>{event.created_at}</td>
            <td>{event.event_type}</td>
            <td>{event.note or ""}</td>
        </tr>
        """

    box_options = ""

    for box in boxes:
        box_options += f"""
        <option value="{box.id}">
            {box.box_code} - {box.temperature} °C - {box.alert_status}
        </option>
        """

    return f"""
    <html>
    <body style="font-family:Arial;background:#f1f5f9;padding:30px;">

        <h1>DxCon Sample Verification</h1>

        <div style="background:white;padding:25px;border-radius:12px;width:520px;">
            <h2>{sample.sample_code}</h2>

            <img src="{qr_url(sample.sample_code)}">

            <p><strong>Patient:</strong> {patient_name}</p>
            <p><strong>Transport Box:</strong> {box_info}</p>
            <p><strong>Status:</strong> {sample.status}</p>
            <p><strong>Latitude:</strong> {sample.latitude or ""}</p>
            <p><strong>Longitude:</strong> {sample.longitude or ""}</p>
            <p>{gps_link}</p>
        </div>

        <br>

        <h2>Chain of Custody Timeline</h2>

        <table border="1" cellpadding="10" style="background:white;width:100%;">
            <tr>
                <th>Time</th>
                <th>Event</th>
                <th>Note</th>
            </tr>
            {event_rows}
        </table>

        <br>
        <a href="/samples">Back to Samples</a>

    </body>
    </html>
    """
