from flask import Blueprint

from app.models.payment import Payment
from app.models.order import Order
from app.models.test_result import TestResult
from app.models.sample_tracking import SampleTracking
from app.models.transport_box import TransportBox
from app.models.driver import Driver
from app.models.dispatch_job import DispatchJob
from app.models.incident import Incident

from app.utils.auth import role_required


executive_web_bp = Blueprint("executive_web", __name__)


@executive_web_bp.route("/executive")
@role_required("SUPER_ADMIN")
def executive():

    revenue = sum(p.amount or 0 for p in Payment.query.all())
    orders = Order.query.count()
    results = TestResult.query.count()

    approved = TestResult.query.filter_by(approval_status="APPROVED").count()
    approval_rate = round(approved / results * 100, 1) if results else 0

    samples = SampleTracking.query.count()
    completed_samples = SampleTracking.query.filter_by(status="COMPLETED").count()
    sample_rate = round(completed_samples / samples * 100, 1) if samples else 0

    alerts = TransportBox.query.filter(
        TransportBox.alert_status != "NORMAL"
    ).count()

    open_incidents = Incident.query.filter_by(status="OPEN").count()
    critical_incidents = Incident.query.filter_by(severity="CRITICAL").count()
    resolved_incidents = Incident.query.filter_by(status="RESOLVED").count()

    drivers = Driver.query.count()

    health_score = 100
    health_score -= alerts * 5
    health_score -= open_incidents * 5
    health_score -= critical_incidents * 10

    if approval_rate < 90:
        health_score -= 10

    if sample_rate < 90:
        health_score -= 10

    if health_score < 0:
        health_score = 0

    field_staff = {}

    for sample in SampleTracking.query.all():
        staff_id = sample.collector_id or "UNASSIGNED"

        if staff_id not in field_staff:
            field_staff[staff_id] = {
                "name": staff_id,
                "samples_assigned": 0,
                "samples_completed": 0,
                "dispatch_jobs": 0,
                "completed_jobs": 0,
                "distance": 0,
                "status": "ACTIVE"
            }

        field_staff[staff_id]["samples_assigned"] += 1

        if sample.status == "COMPLETED":
            field_staff[staff_id]["samples_completed"] += 1

    for driver in Driver.query.all():

        staff_id = driver.driver_code

        if staff_id not in field_staff:
            field_staff[staff_id] = {
                "name": driver.full_name,
                "samples_assigned": 0,
                "samples_completed": 0,
                "dispatch_jobs": 0,
                "completed_jobs": 0,
                "distance": 0,
                "status": driver.status
            }

        jobs = DispatchJob.query.filter_by(driver_id=driver.id).all()

        field_staff[staff_id]["name"] = driver.full_name
        field_staff[staff_id]["status"] = driver.status
        field_staff[staff_id]["dispatch_jobs"] += len(jobs)

        for job in jobs:
            if job.status == "COMPLETED":
                field_staff[staff_id]["completed_jobs"] += 1

            field_staff[staff_id]["distance"] += job.total_distance_km or 0

    staff_rows = ""

    sorted_staff = sorted(
        field_staff.items(),
        key=lambda item: (
            item[1]["samples_assigned"]
            + item[1]["dispatch_jobs"]
        ),
        reverse=True
    )

    for staff_id, data in sorted_staff:

        sample_rate_staff = 0
        if data["samples_assigned"] > 0:
            sample_rate_staff = round(
                data["samples_completed"] /
                data["samples_assigned"] * 100,
                1
            )

        job_rate = 0
        if data["dispatch_jobs"] > 0:
            job_rate = round(
                data["completed_jobs"] /
                data["dispatch_jobs"] * 100,
                1
            )

        staff_rows += f"""
        <tr>
            <td>{data["name"]}</td>
            <td>{staff_id}</td>
            <td>{data["samples_assigned"]}</td>
            <td>{data["samples_completed"]}</td>
            <td>{sample_rate_staff}%</td>
            <td>{data["dispatch_jobs"]}</td>
            <td>{data["completed_jobs"]}</td>
            <td>{job_rate}%</td>
            <td>{round(data["distance"], 1)} km</td>
            <td>{data["status"]}</td>
        </tr>
        """

    return f"""
    <html>
    <head>
        <title>DxCon Executive Dashboard</title>

        <style>
            body {{
                font-family:Arial;
                background:#f1f5f9;
                padding:30px;
            }}

            .cards {{
                display:grid;
                grid-template-columns:repeat(4,1fr);
                gap:20px;
            }}

            .card {{
                background:white;
                padding:25px;
                border-radius:14px;
                box-shadow:0 4px 12px rgba(0,0,0,.08);
            }}

            .title {{
                color:#64748b;
                font-size:14px;
            }}

            .value {{
                font-size:34px;
                font-weight:bold;
                margin-top:10px;
            }}

            .green {{ color:#198754; }}
            .orange {{ color:#f97316; }}
            .red {{ color:#dc3545; }}
            .purple {{ color:#7c3aed; }}

            .section {{
                background:white;
                margin-top:28px;
                padding:24px;
                border-radius:14px;
                box-shadow:0 4px 12px rgba(0,0,0,.08);
                overflow-x:auto;
            }}

            table {{
                width:100%;
                border-collapse:collapse;
                min-width:1000px;
            }}

            th, td {{
                border:1px solid #cbd5e1;
                padding:12px;
                text-align:left;
                font-size:14px;
            }}

            th {{
                background:#e2e8f0;
            }}

            a {{
                color:#0d6efd;
                text-decoration:none;
            }}
        </style>
    </head>

    <body>

        <h1>DxCon CEO Dashboard V3</h1>

        <div class="cards">

            <div class="card">
                <div class="title">Revenue</div>
                <div class="value green">{revenue:,.0f}</div>
            </div>

            <div class="card">
                <div class="title">Orders</div>
                <div class="value">{orders}</div>
            </div>

            <div class="card">
                <div class="title">Approval Rate</div>
                <div class="value purple">{approval_rate}%</div>
            </div>

            <div class="card">
                <div class="title">Sample Completion</div>
                <div class="value orange">{sample_rate}%</div>
            </div>

            <div class="card">
                <div class="title">Temperature Alerts</div>
                <div class="value red">{alerts}</div>
            </div>

            <div class="card">
                <div class="title">Open Incidents</div>
                <div class="value red">{open_incidents}</div>
            </div>

            <div class="card">
                <div class="title">Critical Incidents</div>
                <div class="value red">{critical_incidents}</div>
            </div>

            <div class="card">
                <div class="title">Resolved Incidents</div>
                <div class="value green">{resolved_incidents}</div>
            </div>

            <div class="card">
                <div class="title">System Health</div>
                <div class="value green">{health_score}%</div>
            </div>

        </div>

        <div class="section">
            <h2>Field Staff Performance</h2>

            <table>
                <tr>
                    <th>Name</th>
                    <th>Staff Code</th>
                    <th>Samples Assigned</th>
                    <th>Samples Completed</th>
                    <th>Sample Rate</th>
                    <th>Dispatch Jobs</th>
                    <th>Completed Jobs</th>
                    <th>Job Rate</th>
                    <th>Total Distance</th>
                    <th>Status</th>
                </tr>

                {staff_rows}

            </table>
        </div>

        <br>

        <a href="/dashboard">Dashboard</a>
        |
        <a href="/analytics">Analytics</a>
        |
        <a href="/operations">Operations</a>
        |
        <a href="/incidents">Incidents</a>
        |
        <a href="/collector-kpi">Collector KPI</a>
        |
        <a href="/tat-kpi">TAT KPI</a>

    </body>
    </html>
    """
