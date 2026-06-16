from flask import Blueprint

from app.models.sample_tracking import SampleTracking
from app.utils.auth import role_required


collector_kpi_web_bp = Blueprint(
    "collector_kpi_web",
    __name__
)


@collector_kpi_web_bp.route("/collector-kpi")
@role_required("SUPER_ADMIN")
def collector_kpi():

    samples = SampleTracking.query.all()

    stats = {}

    for sample in samples:
        collector_id = sample.collector_id or "UNASSIGNED"

        if collector_id not in stats:
            stats[collector_id] = {
                "assigned": 0,
                "completed": 0,
                "in_transit": 0,
                "received": 0,
                "checked_in": 0
            }

        stats[collector_id]["assigned"] += 1

        if sample.status == "COMPLETED":
            stats[collector_id]["completed"] += 1

        if sample.status == "IN_TRANSIT":
            stats[collector_id]["in_transit"] += 1

        if sample.status == "RECEIVED":
            stats[collector_id]["received"] += 1

        if sample.status == "CHECKED_IN":
            stats[collector_id]["checked_in"] += 1

    rows = ""

    for collector_id, data in stats.items():

        assigned = data["assigned"]
        completed = data["completed"]

        completion_rate = 0

        if assigned > 0:
            completion_rate = round(
                completed / assigned * 100,
                1
            )

        rows += f"""
        <tr>
            <td><strong>{collector_id}</strong></td>
            <td>{assigned}</td>
            <td>{data["checked_in"]}</td>
            <td>{data["in_transit"]}</td>
            <td>{data["received"]}</td>
            <td>{completed}</td>
            <td>{completion_rate}%</td>
        </tr>
        """

    return f"""
    <html>
    <head>
        <title>Collector KPI</title>
        <style>
            body {{
                font-family: Arial;
                background: #f1f5f9;
                padding: 30px;
                color: #0f172a;
            }}
            .panel {{
                background: white;
                padding: 24px;
                border-radius: 14px;
                box-shadow: 0 4px 12px rgba(0,0,0,.08);
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                background: white;
            }}
            th, td {{
                border: 1px solid #cbd5e1;
                padding: 12px;
                text-align: left;
            }}
            th {{
                background: #e2e8f0;
            }}
            a {{
                color: #0d6efd;
                text-decoration: none;
            }}
        </style>
    </head>
    <body>

        <h1>Collector KPI Dashboard</h1>

        <div class="panel">
            <table>
                <tr>
                    <th>Collector</th>
                    <th>Assigned Samples</th>
                    <th>Checked In</th>
                    <th>In Transit</th>
                    <th>Received</th>
                    <th>Completed</th>
                    <th>Completion Rate</th>
                </tr>
                {rows}
            </table>
        </div>

        <br>
        <a href="/dashboard">Back to Dashboard</a>
        |
        <a href="/operations">Operations Tower</a>

    </body>
    </html>
    """
