from flask import Blueprint

from app.models.sample_event import SampleEvent
from app.models.sample_tracking import SampleTracking
from app.utils.auth import role_required


tat_kpi_web_bp = Blueprint(
    "tat_kpi_web",
    __name__
)


@tat_kpi_web_bp.route("/tat-kpi")
@role_required("SUPER_ADMIN")
def tat_kpi():

    samples = SampleTracking.query.all()

    rows = ""

    total_hours = 0
    tat_count = 0
    fastest = None
    slowest = None

    for sample in samples:

        checked_in = SampleEvent.query.filter_by(
            sample_tracking_id=sample.id,
            event_type="CHECKED_IN"
        ).first()

        approved = SampleEvent.query.filter_by(
            sample_tracking_id=sample.id,
            event_type="DOCTOR_APPROVED"
        ).first()

        if not checked_in or not approved:
            continue

        tat_hours = round(
            (
                approved.created_at -
                checked_in.created_at
            ).total_seconds() / 3600,
            2
        )

        total_hours += tat_hours
        tat_count += 1

        if fastest is None or tat_hours < fastest:
            fastest = tat_hours

        if slowest is None or tat_hours > slowest:
            slowest = tat_hours

        rows += f"""
        <tr>
            <td>{sample.sample_code}</td>
            <td>{checked_in.created_at}</td>
            <td>{approved.created_at}</td>
            <td>{tat_hours} h</td>
        </tr>
        """

    average = round(total_hours / tat_count, 2) if tat_count else 0

    return f"""
    <html>
    <head>
        <title>TAT KPI Dashboard</title>
        <style>
            body {{
                font-family: Arial;
                background: #f1f5f9;
                padding: 30px;
            }}
            .card {{
                background: white;
                padding: 20px;
                border-radius: 12px;
                margin-bottom: 20px;
                box-shadow: 0 4px 12px rgba(0,0,0,.08);
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                background: white;
            }}
            th, td {{
                border: 1px solid #cbd5e1;
                padding: 10px;
            }}
            th {{
                background: #e2e8f0;
            }}
        </style>
    </head>

    <body>

        <h1>DxCon Turnaround Time KPI</h1>

        <div class="card">
            <h3>Average TAT: {average} h</h3>
            <h3>Fastest TAT: {fastest or 0} h</h3>
            <h3>Slowest TAT: {slowest or 0} h</h3>
            <h3>Samples Measured: {tat_count}</h3>
        </div>

        <table>
            <tr>
                <th>Sample</th>
                <th>Checked In</th>
                <th>Doctor Approved</th>
                <th>TAT</th>
            </tr>
            {rows}
        </table>

        <br>
        <a href="/dashboard">Back Dashboard</a>
        |
        <a href="/operations/timeline">Operations Timeline</a>

    </body>
    </html>
    """
