from flask import Blueprint

from app.models.sample_tracking import SampleTracking
from app.models.transport_box import TransportBox
from app.models.driver import Driver
from app.models.test_result import TestResult

operations_web_bp = Blueprint(
    "operations_web",
    __name__
)


@operations_web_bp.route("/operations")
def operations():

    checked_in = SampleTracking.query.filter_by(
        status="CHECKED_IN"
    ).count()

    received = SampleTracking.query.filter_by(
        status="RECEIVED"
    ).count()

    in_transit = SampleTracking.query.filter_by(
        status="IN_TRANSIT"
    ).count()

    completed = SampleTracking.query.filter_by(
        status="COMPLETED"
    ).count()

    drivers = Driver.query.count()

    active_drivers = Driver.query.filter_by(
        status="ACTIVE"
    ).count()

    boxes = TransportBox.query.count()

    temp_alerts = TransportBox.query.filter(
        TransportBox.alert_status != "NORMAL"
    ).count()

    pending_results = TestResult.query.filter_by(
        approval_status="PENDING"
    ).count()

    approved_results = TestResult.query.filter_by(
        approval_status="APPROVED"
    ).count()

    return f"""
    <html>
    <body style="
        font-family:Arial;
        background:#f1f5f9;
        padding:30px;
    ">

        <h1>DxCon Operations Tower</h1>

        <div style="
            display:grid;
            grid-template-columns:repeat(4,1fr);
            gap:20px;
        ">

            <div style="background:white;padding:20px;border-radius:10px;">
                <h3>Checked In</h3>
                <h1>{checked_in}</h1>
            </div>

            <div style="background:white;padding:20px;border-radius:10px;">
                <h3>Received</h3>
                <h1>{received}</h1>
            </div>

            <div style="background:white;padding:20px;border-radius:10px;">
                <h3>In Transit</h3>
                <h1>{in_transit}</h1>
            </div>

            <div style="background:white;padding:20px;border-radius:10px;">
                <h3>Completed</h3>
                <h1>{completed}</h1>
            </div>

            <div style="background:white;padding:20px;border-radius:10px;">
                <h3>Drivers</h3>
                <h1>{active_drivers}/{drivers}</h1>
            </div>

            <div style="background:white;padding:20px;border-radius:10px;">
                <h3>Transport Boxes</h3>
                <h1>{boxes}</h1>
            </div>

            <div style="background:white;padding:20px;border-radius:10px;">
                <h3>Temperature Alerts</h3>
                <h1 style="color:red;">{temp_alerts}</h1>
            </div>

            <div style="background:white;padding:20px;border-radius:10px;">
                <h3>Pending Results</h3>
                <h1>{pending_results}</h1>
            </div>

        </div>

        <br>

        <div style="
            background:white;
            padding:20px;
            border-radius:10px;
        ">
            <h2>Doctor Approval</h2>

            Approved:
            <b>{approved_results}</b>

            <br><br>

            Pending:
            <b>{pending_results}</b>
        </div>

    </body>
    </html>
    """
