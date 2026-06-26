from flask import Blueprint, redirect

from app.extensions.db import db
from app.models.driver import Driver
from app.models.home_collection import HomeCollection
from app.models.sample_tracking import SampleTracking
from app.models.shipment import Shipment
from app.core.statuses import (
    SHIPMENT_ACCEPTED,
    SHIPMENT_CREATED,
    VALID_COLLECTOR_SHIPMENT_STATUSES,
)


collector_mobile_web_bp = Blueprint(
    "collector_mobile_web",
    __name__
)


def btn(url, text, color="#0d6efd"):
    return f"""
    <a href="{url}" style="
        display:inline-block;
        background:{color};
        color:white;
        padding:10px 14px;
        border-radius:8px;
        text-decoration:none;
        margin:4px 0;
        font-weight:bold;
    ">{text}</a>
    """


@collector_mobile_web_bp.route("/collector-mobile")
def collector_mobile():

    collectors = Driver.query.all()
    jobs = HomeCollection.query.all()
    samples = SampleTracking.query.order_by(
        SampleTracking.updated_at.desc()
    ).all()

    if not collectors:
        collector_block = """
        <div class="card">
            <h2>No Collector</h2>
            <p>No collector found.</p>
            <a class="primary" href="/collector-mobile/create-demo">
                Create Demo Collector
            </a>
        </div>
        """
    else:
        collector_block = "<div class='card'><h2>Collectors</h2>"
        for c in collectors:
            collector_block += f"""
            <div class="item">
                <b>{c.driver_code}</b><br>
                {c.full_name}<br>
                {c.phone or ""}<br>
                Vehicle: {c.vehicle_no or ""}
            </div>
            """
        collector_block += "</div>"

    job_rows = ""

    for job in jobs:
        collector_id = getattr(job, "collector_id", None)

        assign_buttons = ""

        for c in collectors:
            assign_buttons += btn(
                f"/api/v1/workflow/assign/{job.id}/{c.id}",
                f"Assign {c.driver_code}",
                "#7c3aed"
            )

        job_rows += f"""
        <div class="card">
            <h2>Booking</h2>
            <p><b>Address:</b> {job.address}</p>
            <p><b>Schedule:</b> {job.scheduled_time}</p>
            <p><b>Status:</b> {job.status}</p>
            <p><b>Collector:</b> {collector_id or "Unassigned"}</p>

            <div>{assign_buttons}</div>

            {btn(f"/api/v1/workflow/checkin/{job.id}", "Check In", "#198754")}
            {btn(f"/api/v1/workflow/collected/{job.id}", "Collected", "#f97316")}
        </div>
        """

    shipments = Shipment.query.filter(
        Shipment.status.in_(VALID_COLLECTOR_SHIPMENT_STATUSES)
    ).order_by(
        Shipment.created_at.desc()
    ).all()

    shipment_rows = ""

    for shipment in shipments:
        actions = ""

        if shipment.status == SHIPMENT_CREATED:
            actions += btn(
                f"/shipments/{shipment.id}/accept",
                "Accept Shipment",
                "#198754",
            )

        if shipment.status == SHIPMENT_ACCEPTED:
            actions += btn(
                f"/shipments/{shipment.id}/start-trip",
                "Start Trip",
                "#f97316",
            )

        shipment_rows += f"""
        <div class="card">
            <h2>{shipment.shipment_code}</h2>
            <p><b>Status:</b> {shipment.status}</p>
            <p><b>Lab:</b> {shipment.lab_name or ""}</p>
            <p><b>Collector:</b> {shipment.collector_id or "Unassigned"}</p>
            <p><b>Box:</b> {shipment.transport_box_id or ""}</p>
            <p><b>GPS:</b> {shipment.gps_location or "0.0,0.0"}</p>
            <div>{actions}</div>
            {btn(f"/shipments/{shipment.id}", "View Detail", "#0a4b5c")}
        </div>
        """

    sample_rows = ""

    for s in samples:
        map_link = ""

        if s.map_url():
            map_link = btn(s.map_url(), "Open Map", "#0d6efd")

        sample_rows += f"""
        <div class="card">
            <h2>{s.sample_code}</h2>
            <p><b>Status:</b> {s.status}</p>
            <p><b>Collector:</b> {s.collector_id or ""}</p>
            <p><b>Box:</b> {s.transport_box_id or ""}</p>
            <p><b>Updated:</b> {s.updated_at}</p>

            {map_link}

            {btn(f"/api/v1/workflow/sample/{s.id}/RECEIVED", "Received Lab", "#7c3aed")}
            {btn(f"/api/v1/workflow/sample/{s.id}/PROCESSING", "Processing", "#0d6efd")}
            {btn(f"/api/v1/workflow/sample/{s.id}/COMPLETED", "Completed", "#198754")}
        </div>
        """

    return f"""
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1">

        <style>
            body {{
                font-family: Arial;
                background: #f1f5f9;
                margin: 0;
                padding: 16px;
            }}

            .header {{
                background: #0a4b5c;
                color: white;
                padding: 18px;
                border-radius: 14px;
                margin-bottom: 16px;
            }}

            .card {{
                background: white;
                padding: 16px;
                border-radius: 14px;
                margin-bottom: 14px;
                box-shadow: 0 4px 12px rgba(0,0,0,.08);
            }}

            .item {{
                padding: 12px;
                background: #f8fafc;
                border-radius: 10px;
                margin-bottom: 10px;
            }}

            .primary {{
                display: inline-block;
                background: #0d6efd;
                color: white;
                padding: 12px 16px;
                border-radius: 8px;
                text-decoration: none;
                font-weight: bold;
            }}

            h1, h2 {{
                margin-top: 0;
            }}
        </style>
    </head>

    <body>
        <div class="header">
            <h1>DxCon Collector Mobile</h1>
            <p>Field collection workflow</p>
        </div>

        {collector_block}

        <div class="card">
            <h2>Collection Jobs</h2>
            <p>Total: {len(jobs)}</p>
        </div>

        {job_rows}

        <div class="card">
            <h2>Shipments (FP-003)</h2>
            <p>Total: {len(shipments)}</p>
            <p>Accept assigned shipments, then start the trip to lab.</p>
        </div>

        {shipment_rows}

        <div class="card">
            <h2>Samples</h2>
            <p>Total: {len(samples)}</p>
        </div>

        {sample_rows}

        <br>
        <a href="/shipments">Shipments</a> |
        <a href="/logistics">Logistics Dashboard</a>
    </body>
    </html>
    """


@collector_mobile_web_bp.route("/collector-mobile/create-demo")
def create_demo_collector():

    c = Driver.query.filter_by(
        driver_code="COL-DEMO-001"
    ).first()

    if not c:
        c = Driver(
            driver_code="COL-DEMO-001",
            full_name="DxCon Demo Collector",
            phone="0908888888",
            vehicle_no="59A-12345",
            status="ACTIVE"
        )

        db.session.add(c)
        db.session.commit()

    return redirect("/collector-mobile")
