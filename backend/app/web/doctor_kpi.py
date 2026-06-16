from flask import Blueprint

from app.models.test_result import TestResult
from app.utils.auth import role_required

doctor_kpi_web_bp = Blueprint(
    "doctor_kpi_web",
    __name__
)

@doctor_kpi_web_bp.route("/doctor/kpi")
@role_required("SUPER_ADMIN","DOCTOR")
def doctor_kpi():

    pending = TestResult.query.filter_by(
        approval_status="PENDING"
    ).count()

    approved = TestResult.query.filter_by(
        approval_status="APPROVED"
    ).count()

    critical = TestResult.query.filter(
        TestResult.flag != "NORMAL"
    ).count()

    total = pending + approved

    approval_rate = 0

    if total > 0:
        approval_rate = round(
            approved * 100 / total,
            1
        )

    return f"""
    <html>
    <head>

        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>

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
                border-radius:12px;
                box-shadow:0 4px 12px rgba(0,0,0,.08);
            }}

            .value {{
                font-size:32px;
                font-weight:bold;
                color:#0d6efd;
            }}

            .chart {{
                background:white;
                padding:20px;
                border-radius:12px;
                margin-top:25px;
            }}

        </style>

    </head>

    <body>

        <h1>Doctor KPI Dashboard</h1>

        <div class="cards">

            <div class="card">
                <h3>Pending</h3>
                <div class="value">{pending}</div>
            </div>

            <div class="card">
                <h3>Approved</h3>
                <div class="value">{approved}</div>
            </div>

            <div class="card">
                <h3>Critical</h3>
                <div class="value">{critical}</div>
            </div>

            <div class="card">
                <h3>Approval Rate</h3>
                <div class="value">{approval_rate}%</div>
            </div>

        </div>

        <div class="chart">
            <canvas id="doctorChart"></canvas>
        </div>

        <script>

        new Chart(
            document.getElementById("doctorChart"),
            {{
                type:"bar",
                data:{{
                    labels:[
                        "Pending",
                        "Approved",
                        "Critical"
                    ],
                    datasets:[{{
                        label:"Results",
                        data:[
                            {pending},
                            {approved},
                            {critical}
                        ]
                    }}]
                }}
            }}
        )

        </script>

        <br>

        <a href="/doctor">
            Back Doctor Portal
        </a>

    </body>
    </html>
    """
