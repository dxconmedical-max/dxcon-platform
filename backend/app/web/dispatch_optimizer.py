from flask import Blueprint, request, redirect

from app.extensions.db import db
from app.models.dispatch_job import DispatchJob
from app.models.dispatch_item import DispatchItem
from app.models.driver import Driver
from app.models.transport_box import TransportBox
from app.models.sample_tracking import SampleTracking
from app.models.home_collection import HomeCollection
from app.models.patient import Patient
from app.utils.auth import role_required

import uuid


dispatch_optimizer_web_bp = Blueprint(
    "dispatch_optimizer_web",
    __name__
)


def google_route_url(job):

    points = []

    if job.start_latitude and job.start_longitude:
        points.append(f"{job.start_latitude},{job.start_longitude}")

    items = DispatchItem.query.filter_by(
        dispatch_job_id=job.id
    ).order_by(DispatchItem.sequence_no.asc()).all()

    for item in items:
        sample = SampleTracking.query.get(item.sample_tracking_id)
        if sample and sample.latitude and sample.longitude:
            points.append(f"{sample.latitude},{sample.longitude}")

    if job.destination_latitude and job.destination_longitude:
        points.append(f"{job.destination_latitude},{job.destination_longitude}")

    if len(points) < 2:
        return ""

    return "https://www.google.com/maps/dir/" + "/".join(points)


@dispatch_optimizer_web_bp.route("/dispatch-jobs")
@role_required("SUPER_ADMIN", "COLLECTOR", "LAB_TECHNICIAN")
def dispatch_jobs_page():

    jobs = DispatchJob.query.all()
    rows = ""

    for job in jobs:

        driver = Driver.query.get(job.driver_id) if job.driver_id else None
        box = TransportBox.query.get(job.transport_box_id) if job.transport_box_id else None

        items = DispatchItem.query.filter_by(dispatch_job_id=job.id).all()

        route = google_route_url(job)
        route_link = ""

        if route:
            route_link = f"""
            <a target="_blank" href="{route}">
                View Route
            </a>
            """

        rows += f"""
        <tr>
            <td>{job.job_code}</td>
            <td>{driver.full_name if driver else ""}</td>
            <td>{box.box_code if box else ""}</td>
            <td>{len(items)}</td>
            <td>{job.status}</td>
            <td>{job.total_distance_km} km</td>
            <td>{job.estimated_minutes} min</td>
            <td>
                <a href="/dispatch-jobs/{job.id}">Detail</a>
                |
                {route_link}
            </td>
        </tr>
        """

    return f"""
    <html>
    <body style="font-family:Arial;background:#f1f5f9;padding:30px;">

        <h1>Dispatch Route Optimizer</h1>

        <a href="/dispatch-jobs/new"
           style="background:#0d6efd;color:white;padding:10px 15px;text-decoration:none;border-radius:6px;">
           + New Dispatch Job
        </a>

        <br><br>

        <table border="1" cellpadding="10" style="background:white;width:100%;">
            <tr>
                <th>Job Code</th>
                <th>Driver</th>
                <th>Box</th>
                <th>Samples</th>
                <th>Status</th>
                <th>Distance</th>
                <th>ETA</th>
                <th>Action</th>
            </tr>
            {rows}
        </table>

        <br>
        <a href="/dashboard">Back to Dashboard</a>

    </body>
    </html>
    """


@dispatch_optimizer_web_bp.route("/dispatch-jobs/new", methods=["GET", "POST"])
@role_required("SUPER_ADMIN", "COLLECTOR")
def new_dispatch_job():

    drivers = Driver.query.all()
    boxes = TransportBox.query.all()
    samples = SampleTracking.query.all()

    if request.method == "POST":

        job = DispatchJob(
            job_code="DSP-" + str(uuid.uuid4())[:8].upper(),
            driver_id=request.form.get("driver_id"),
            transport_box_id=request.form.get("transport_box_id"),
            start_latitude=request.form.get("start_latitude"),
            start_longitude=request.form.get("start_longitude"),
            destination_latitude=request.form.get("destination_latitude"),
            destination_longitude=request.form.get("destination_longitude"),
            total_distance_km=float(request.form.get("total_distance_km") or 0),
            estimated_minutes=int(request.form.get("estimated_minutes") or 0),
            status="PLANNED"
        )

        db.session.add(job)
        db.session.commit()

        selected_samples = request.form.getlist("sample_ids")

        seq = 1

        for sample_id in selected_samples:
            item = DispatchItem(
                dispatch_job_id=job.id,
                sample_tracking_id=sample_id,
                sequence_no=seq,
                status="ASSIGNED"
            )

            db.session.add(item)
            seq += 1

        db.session.commit()

        return redirect("/dispatch-jobs")

    driver_options = ""
    for driver in drivers:
        driver_options += f"""
        <option value="{driver.id}">
            {driver.driver_code} - {driver.full_name}
        </option>
        """

    box_options = ""
    for box in boxes:
        box_options += f"""
        <option value="{box.id}">
            {box.box_code} - {box.temperature} °C - {box.alert_status}
        </option>
        """

    sample_options = ""
    for sample in samples:

        patient_name = ""

        if sample.home_collection_id:
            collection = HomeCollection.query.get(sample.home_collection_id)

            if collection:
                patient = Patient.query.get(collection.patient_id)
                patient_name = patient.full_name if patient else ""

        sample_options += f"""
        <label>
            <input type="checkbox" name="sample_ids" value="{sample.id}">
            {sample.sample_code} - {patient_name} - {sample.status}
        </label><br>
        """

    return f"""
    <html>
    <body style="font-family:Arial;background:#f1f5f9;padding:30px;">

        <h1>New Dispatch Job</h1>

        <form method="POST">

            <label>Driver</label><br>
            <select name="driver_id">
                {driver_options}
            </select>

            <br><br>

            <label>Transport Box</label><br>
            <select name="transport_box_id">
                {box_options}
            </select>

            <br><br>

            <label>Samples</label><br>
            {sample_options}

            <br>

            <label>Start Latitude</label><br>
            <input name="start_latitude" placeholder="10.7769">

            <br><br>

            <label>Start Longitude</label><br>
            <input name="start_longitude" placeholder="106.7009">

            <br><br>

            <label>Destination Latitude</label><br>
            <input name="destination_latitude" placeholder="10.762622">

            <br><br>

            <label>Destination Longitude</label><br>
            <input name="destination_longitude" placeholder="106.660172">

            <br><br>

            <label>Estimated Distance KM</label><br>
            <input name="total_distance_km" placeholder="14.5">

            <br><br>

            <label>ETA Minutes</label><br>
            <input name="estimated_minutes" placeholder="42">

            <br><br>

            <button type="submit">Create Dispatch Job</button>

        </form>

        <br>
        <a href="/dispatch-jobs">Back</a>

    </body>
    </html>
    """


@dispatch_optimizer_web_bp.route("/dispatch-jobs/<job_id>")
@role_required("SUPER_ADMIN", "COLLECTOR", "LAB_TECHNICIAN")
def dispatch_job_detail(job_id):

    job = DispatchJob.query.get(job_id)

    if not job:
        return "Dispatch job not found"

    driver = Driver.query.get(job.driver_id) if job.driver_id else None
    box = TransportBox.query.get(job.transport_box_id) if job.transport_box_id else None

    items = DispatchItem.query.filter_by(
        dispatch_job_id=job.id
    ).order_by(DispatchItem.sequence_no.asc()).all()

    rows = ""

    for item in items:

        sample = SampleTracking.query.get(item.sample_tracking_id)
        sample_code = sample.sample_code if sample else ""

        rows += f"""
        <tr>
            <td>{item.sequence_no}</td>
            <td>{sample_code}</td>
            <td>{item.status}</td>
            <td>
                <a href="/samples/verify/{sample_code}">
                    Verify
                </a>
            </td>
        </tr>
        """

    route = google_route_url(job)

    route_link = ""

    if route:
        route_link = f"""
        <a target="_blank" href="{route}">
            Open Optimized Route
        </a>
        """

    return f"""
    <html>
    <body style="font-family:Arial;background:#f1f5f9;padding:30px;">

        <h1>Dispatch Job - {job.job_code}</h1>

        <p><strong>Driver:</strong> {driver.full_name if driver else ""}</p>
        <p><strong>Box:</strong> {box.box_code if box else ""}</p>
        <p><strong>Status:</strong> {job.status}</p>
        <p><strong>Distance:</strong> {job.total_distance_km} km</p>
        <p><strong>ETA:</strong> {job.estimated_minutes} minutes</p>
        <p>{route_link}</p>

        <h2>Samples Route Sequence</h2>

        <table border="1" cellpadding="10" style="background:white;width:100%;">
            <tr>
                <th>Sequence</th>
                <th>Sample</th>
                <th>Status</th>
                <th>Action</th>
            </tr>
            {rows}
        </table>

        <br>
        <a href="/dispatch-jobs">Back to Dispatch Jobs</a>

    </body>
    </html>
    """
