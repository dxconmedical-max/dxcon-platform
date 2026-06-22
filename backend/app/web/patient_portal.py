from flask import Blueprint, session, redirect

from app.models.patient import Patient
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.test_result import TestResult
from app.models.home_collection import HomeCollection
from app.models.sample_tracking import SampleTracking
from app.models.sample_event import SampleEvent
from app.models.clinical_summary import ClinicalSummary
from app.models.result_file import ResultFile

patient_portal_web_bp = Blueprint(
    "patient_portal_web",
    __name__
)

@patient_portal_web_bp.route("/portal/<patient_id>")
def patient_portal(patient_id):

    patient = Patient.query.get(patient_id)

    if not patient:
        return "Patient not found"

    orders = Order.query.filter_by(
        patient_id=patient_id
    ).all()

    order_rows = ""

    for order in orders:

        file_links = ""

        files = ResultFile.query.filter_by(
            order_id=order.id
        ).all()

        for f in files:
            file_links += f"""
            <a href="/portal/result-files/download/{f.id}">
                {f.file_name}
            </a><br>
            """

        order_rows += f"""
        <tr>
            <td>{order.order_code}</td>
            <td>{order.status}</td>
            <td>{order.total_amount:,.0f}</td>

            <td>
                <a href="/results/report/{order.id}">
                    View Report
                </a>
            </td>

            <td>
                <a href="/results/report/{order.id}/pdf">
                    PDF
                </a>
            </td>

            <td>
                <a href="/api/v1/ai-v2/order/{order.id}">
                    Generate AI
                </a>
            </td>

            <td>
                {file_links or "No file"}
            </td>
        </tr>
        """

    results_rows = ""

    for order in orders:

        items = OrderItem.query.filter_by(
            order_id=order.id
        ).all()

        for item in items:

            result = TestResult.query.filter_by(
                order_item_id=item.id
            ).first()

            if result:

                verify_link = (
                    f"/results/verify/{result.id}"
                )

                results_rows += f"""
                <tr>
                    <td>{result.test_name}</td>
                    <td>{result.result_value}</td>
                    <td>{result.unit}</td>
                    <td>{result.reference_range}</td>
                    <td>{result.flag}</td>
                    <td>
                        <a href="{verify_link}">
                            Verify
                        </a>
                    </td>
                </tr>
                """

    collections = HomeCollection.query.filter_by(
        patient_id=patient_id
    ).all()

    clinical_summary_rows = ""

    for order in orders:
        summary = ClinicalSummary.query.filter_by(
            order_id=order.id
        ).first()

        if summary:
            clinical_summary_rows += f"""
            <div style="background:#f8fafc;padding:18px;border-radius:10px;margin-bottom:15px;">
                <h3>Order: {order.order_code}</h3>
                <p><b>Risk Level:</b> {summary.risk_level}</p>
                <p><b>Findings:</b><br>{summary.findings or ""}</p>
                <p><b>Recommendations:</b><br>{summary.recommendations or ""}</p>
            </div>
            """

    collection_rows = ""

    for item in collections:

        collection_rows += f"""
        <tr>
            <td>{item.address}</td>
            <td>{item.scheduled_time}</td>
            <td>{item.status}</td>
        </tr>
        """

    timeline_rows = ""

    samples = SampleTracking.query.all()

    for sample in samples:
        events = SampleEvent.query.filter_by(
            sample_tracking_id=sample.id
        ).order_by(
            SampleEvent.created_at.asc()
        ).all()

        if events:
            timeline_rows += f"""
            <h3>Sample: {sample.sample_code}</h3>
            """

        for event in events:

            color = "#0d6efd"

            if event.event_type == "CHECKED_IN":
                color = "#198754"
            elif event.event_type == "IN_TRANSIT":
                color = "#f97316"
            elif event.event_type == "RECEIVED":
                color = "#7c3aed"
            elif event.event_type == "PROCESSING":
                color = "#0d6efd"
            elif event.event_type == "RESULT_CREATED":
                color = "#0891b2"
            elif event.event_type == "DOCTOR_APPROVED":
                color = "#198754"

            timeline_rows += f"""
            <div style="border-left:6px solid {color};background:#f8fafc;padding:14px;margin-bottom:12px;border-radius:8px;">
                <b>{event.event_type}</b><br>
                {event.note or ""}<br>
                <small>{event.created_at}</small>
            </div>
            """

    tracking_rows = ""

    for sample in SampleTracking.query.all():

        tracking_rows += f"""
        <tr>
            <td>{sample.sample_code}</td>
            <td>{sample.status}</td>
            <td>{sample.map_url() or ''}</td>
        </tr>
        """

    return f"""
    <html>
    <head>
        <title>DxCon Patient Portal</title>

        <style>
            body {{
                font-family:Arial;
                background:#f1f5f9;
                padding:30px;
            }}

            .card {{
                background:white;
                padding:25px;
                border-radius:12px;
                margin-bottom:25px;
                box-shadow:0 4px 12px rgba(0,0,0,.08);
            }}

            table {{
                width:100%;
                border-collapse:collapse;
            }}

            th, td {{
                border:1px solid #cbd5e1;
                padding:10px;
            }}

            th {{
                background:#e2e8f0;
            }}

            h2 {{
                color:#0a4b5c;
            }}
        </style>
    </head>

    <body>

        <h1>DxCon Patient Portal</h1>

        <div class="card">
            <h2>Patient Information</h2>

            <p><b>Code:</b> {patient.patient_code}</p>
            <p><b>Name:</b> {patient.full_name}</p>
            <p><b>Phone:</b> {patient.phone}</p>
        </div>

        <div class="card">
            <h2>Orders</h2>

            <table>
                <tr>
                    <th>Order</th>
                    <th>Status</th>
                    <th>Amount</th>
                    <th>Report</th>
                    <th>PDF</th>
                    <th>AI</th>
                    <th>Files</th>
                    <th>Uploaded Files</th>
                </tr>

                {order_rows}
            </table>
        </div>

        <div class="card">
            <h2>Results</h2>

            <table>
                <tr>
                    <th>Test</th>
                    <th>Result</th>
                    <th>Unit</th>
                    <th>Reference</th>
                    <th>Flag</th>
                    <th>Verify</th>
                </tr>

                {results_rows}
            </table>
        </div>

        <div class="card">
            <h2>Clinical Summary</h2>
            {clinical_summary_rows}
        </div>

        <div class="card">
            <h2>Home Collection</h2>

            <table>
                <tr>
                    <th>Address</th>
                    <th>Schedule</th>
                    <th>Status</th>
                </tr>

                {collection_rows}
            </table>
        </div>

        <div class="card">
            <h2>Patient Timeline</h2>
            {timeline_rows}
        </div>

        <div class="card">
            <h2>Sample Tracking</h2>

            <table>
                <tr>
                    <th>Sample</th>
                    <th>Status</th>
                    <th>Map</th>
                </tr>

                {tracking_rows}
            </table>
        </div>

    </body>
    </html>
    """



@patient_portal_web_bp.route("/my-portal")
def my_patient_portal():

    patient_id = session.get("patient_id")

    if not patient_id:
        return redirect("/login")

    return patient_portal(patient_id)

from flask import session, redirect

