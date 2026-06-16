from flask import Blueprint

from app.models.patient import Patient
from app.models.company import Company
from app.models.order import Order
from app.models.invoice import Invoice
from app.models.payment import Payment
from app.models.test_result import TestResult
from app.models.sample_tracking import SampleTracking
from app.models.transport_box import TransportBox
from app.models.alert import Alert
from app.models.dispatch_job import DispatchJob
from app.models.driver import Driver
from app.utils.auth import role_required


dashboard_web_bp = Blueprint("dashboard_web", __name__)


@dashboard_web_bp.route("/dashboard")
@role_required("SUPER_ADMIN")
def dashboard():

    patient_count = Patient.query.count()
    company_count = Company.query.count()
    order_count = Order.query.count()
    invoice_count = Invoice.query.count()
    payment_count = Payment.query.count()
    result_count = TestResult.query.count()

    pending_orders = Order.query.filter_by(status="PENDING").count()
    completed_orders = Order.query.filter_by(status="COMPLETED").count()

    unpaid_invoices = Invoice.query.filter_by(payment_status="UNPAID").count()
    paid_invoices = Invoice.query.filter_by(payment_status="PAID").count()

    pending_results = TestResult.query.filter_by(approval_status="PENDING").count()
    approved_results = TestResult.query.filter_by(approval_status="APPROVED").count()

    sample_count = SampleTracking.query.count()
    in_transit_samples = SampleTracking.query.filter_by(status="IN_TRANSIT").count()
    received_samples = SampleTracking.query.filter_by(status="RECEIVED").count()
    completed_samples = SampleTracking.query.filter_by(status="COMPLETED").count()
    checked_in_samples = SampleTracking.query.filter_by(status="CHECKED_IN").count()

    box_count = TransportBox.query.count()
    temp_alerts = TransportBox.query.filter(
        TransportBox.alert_status != "NORMAL"
    ).count()

    alert_count = Alert.query.filter_by(status="OPEN").count()
    dispatch_count = DispatchJob.query.count()
    planned_dispatch = DispatchJob.query.filter_by(status="PLANNED").count()
    driver_count = Driver.query.count()
    active_drivers = Driver.query.filter_by(status="ACTIVE").count()

    revenue = sum(payment.amount or 0 for payment in Payment.query.all())

    approval_rate = 0
    if result_count > 0:
        approval_rate = round((approved_results / result_count) * 100, 1)

    return f"""
    <html>
    <head>
        <title>DxCon Executive Dashboard</title>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
            body {{
                margin:0;
                font-family:Arial,sans-serif;
                background:#f1f5f9;
                color:#0f172a;
            }}
            .layout {{
                display:flex;
                min-height:100vh;
            }}
            .sidebar {{
                width:250px;
                background:#0a4b5c;
                color:white;
                padding:24px;
            }}
            .sidebar h2 {{
                margin-top:0;
                margin-bottom:24px;
            }}
            .menu a {{
                display:block;
                color:white;
                text-decoration:none;
                padding:10px 0;
                border-bottom:1px solid rgba(255,255,255,.15);
                font-size:14px;
            }}
            .content {{
                flex:1;
                padding:32px;
            }}
            .section-title {{
                margin-top:32px;
                margin-bottom:16px;
                color:#0a4b5c;
            }}
            .cards {{
                display:grid;
                grid-template-columns:repeat(4,1fr);
                gap:18px;
                margin-bottom:24px;
            }}
            .card {{
                background:white;
                padding:22px;
                border-radius:14px;
                box-shadow:0 4px 12px rgba(0,0,0,.08);
            }}
            .label {{
                color:#64748b;
                font-size:14px;
                margin-bottom:8px;
            }}
            .value {{
                font-size:28px;
                font-weight:bold;
                color:#0d6efd;
            }}
            .green {{ color:#198754; }}
            .orange {{ color:#f97316; }}
            .red {{ color:#dc3545; }}
            .purple {{ color:#7c3aed; }}
            .charts {{
                display:grid;
                grid-template-columns:repeat(2,1fr);
                gap:22px;
                margin-top:20px;
            }}
            .chart-box {{
                background:white;
                padding:22px;
                border-radius:14px;
                box-shadow:0 4px 12px rgba(0,0,0,.08);
            }}
            canvas {{
                width:100% !important;
                height:260px !important;
            }}
            .quick-links {{
                background:white;
                padding:20px;
                border-radius:14px;
                box-shadow:0 4px 12px rgba(0,0,0,.08);
                margin-top:24px;
            }}
            .quick-links a {{
                display:inline-block;
                margin:6px 10px 6px 0;
                padding:9px 12px;
                border-radius:8px;
                background:#e2e8f0;
                color:#0f172a;
                text-decoration:none;
                font-size:14px;
            }}
        </style>
    </head>

    <body>
        <div class="layout">
            <div class="sidebar">
                <h2>DxCon</h2>

                <div class="menu">
                    <a href="/dashboard">Dashboard</a>
                    <a href="/operations">Operations Tower</a>
                    <a href="/analytics">Analytics</a>
                    <a href="/alerts">Alert Center</a>
                    <a href="/operations/timeline">Operations Timeline</a>
                    <a href="/patients">Patients</a>
                    <a href="/companies">Companies</a>
                    <a href="/contracts">Contracts</a>
                    <a href="/orders">Orders</a>
                    <a href="/results">Results</a>
                    <a href="/doctor">Doctor Portal</a>
                    <a href="/collector">Collector Portal</a>
                    <a href="/portal">Patient Portal</a>
                    <a href="/home-collections">Home Collections</a>
                    <a href="/samples">Sample Tracking</a>
                    <a href="/transport-boxes">Transport Boxes</a>
                    <a href="/drivers">Drivers</a>
                    <a href="/dispatch">Dispatch Center</a>
                    <a href="/dispatch-jobs">Route Optimizer</a>
                    <a href="/lab-worklist">Lab Worklist</a>
                    <a href="/result-files">Result Files</a>
                    <a href="/invoices">Invoices</a>
                    <a href="/payments">Payments</a>
                    <a href="/logout">Logout</a>
                </div>
            </div>

            <div class="content">
                <h1>DxCon Executive Dashboard</h1>

                <h2 class="section-title">Executive KPIs</h2>

                <div class="cards">
                    <div class="card"><div class="label">Total Revenue</div><div class="value green">{revenue:,.0f} VND</div></div>
                    <div class="card"><div class="label">Orders</div><div class="value">{order_count}</div></div>
                    <div class="card"><div class="label">Samples</div><div class="value purple">{sample_count}</div></div>
                    <div class="card"><div class="label">Open Alerts</div><div class="value red">{alert_count}</div></div>
                </div>

                <h2 class="section-title">Business Operations</h2>

                <div class="cards">
                    <div class="card"><div class="label">Patients</div><div class="value">{patient_count}</div></div>
                    <div class="card"><div class="label">Companies</div><div class="value">{company_count}</div></div>
                    <div class="card"><div class="label">Invoices</div><div class="value">{invoice_count}</div></div>
                    <div class="card"><div class="label">Payments</div><div class="value">{payment_count}</div></div>

                    <div class="card"><div class="label">Pending Orders</div><div class="value orange">{pending_orders}</div></div>
                    <div class="card"><div class="label">Completed Orders</div><div class="value green">{completed_orders}</div></div>
                    <div class="card"><div class="label">Unpaid Invoices</div><div class="value red">{unpaid_invoices}</div></div>
                    <div class="card"><div class="label">Paid Invoices</div><div class="value green">{paid_invoices}</div></div>
                </div>

                <h2 class="section-title">Laboratory & AI</h2>

                <div class="cards">
                    <div class="card"><div class="label">Total Results</div><div class="value purple">{result_count}</div></div>
                    <div class="card"><div class="label">Pending Results</div><div class="value red">{pending_results}</div></div>
                    <div class="card"><div class="label">Approved Results</div><div class="value green">{approved_results}</div></div>
                    <div class="card"><div class="label">Doctor Approval Rate</div><div class="value green">{approval_rate}%</div></div>
                </div>

                <h2 class="section-title">IoT & Logistics</h2>

                <div class="cards">
                    <div class="card"><div class="label">Checked In Samples</div><div class="value">{checked_in_samples}</div></div>
                    <div class="card"><div class="label">Samples Received</div><div class="value purple">{received_samples}</div></div>
                    <div class="card"><div class="label">Samples In Transit</div><div class="value orange">{in_transit_samples}</div></div>
                    <div class="card"><div class="label">Samples Completed</div><div class="value green">{completed_samples}</div></div>

                    <div class="card"><div class="label">Transport Boxes</div><div class="value">{box_count}</div></div>
                    <div class="card"><div class="label">Temperature Alerts</div><div class="value red">{temp_alerts}</div></div>
                    <div class="card"><div class="label">Dispatch Jobs</div><div class="value purple">{dispatch_count}</div></div>
                    <div class="card"><div class="label">Drivers Active</div><div class="value green">{active_drivers}/{driver_count}</div></div>
                </div>

                <h2 class="section-title">Charts</h2>

                <div class="charts">
                    <div class="chart-box">
                        <h3>Orders by Status</h3>
                        <canvas id="ordersChart"></canvas>
                    </div>

                    <div class="chart-box">
                        <h3>Sample Logistics</h3>
                        <canvas id="samplesChart"></canvas>
                    </div>

                    <div class="chart-box">
                        <h3>Result Approval</h3>
                        <canvas id="resultsChart"></canvas>
                    </div>

                    <div class="chart-box">
                        <h3>IoT Alert Status</h3>
                        <canvas id="iotChart"></canvas>
                    </div>
                </div>

                <div class="quick-links">
                    <h3>Quick Actions</h3>
                    <a href="/orders/new">New Order</a>
                    <a href="/samples/new">New Sample</a>
                    <a href="/dispatch-jobs/new">New Dispatch Job</a>
                    <a href="/results/new">New Result</a>
                    <a href="/alerts">View Alerts</a>
                    <a href="/operations">Operations Tower</a>
                </div>
            </div>
        </div>

        <script>
            new Chart(document.getElementById('ordersChart'), {{
                type: 'bar',
                data: {{
                    labels: ['Pending', 'Completed'],
                    datasets: [{{
                        label: 'Orders',
                        data: [{pending_orders}, {completed_orders}]
                    }}]
                }}
            }});

            new Chart(document.getElementById('samplesChart'), {{
                type: 'bar',
                data: {{
                    labels: ['Checked In', 'Received', 'In Transit', 'Completed'],
                    datasets: [{{
                        label: 'Samples',
                        data: [{checked_in_samples}, {received_samples}, {in_transit_samples}, {completed_samples}]
                    }}]
                }}
            }});

            new Chart(document.getElementById('resultsChart'), {{
                type: 'doughnut',
                data: {{
                    labels: ['Pending', 'Approved'],
                    datasets: [{{
                        label: 'Results',
                        data: [{pending_results}, {approved_results}]
                    }}]
                }}
            }});

            new Chart(document.getElementById('iotChart'), {{
                type: 'doughnut',
                data: {{
                    labels: ['Normal Boxes', 'Temperature Alerts'],
                    datasets: [{{
                        label: 'IoT',
                        data: [{max(box_count - temp_alerts, 0)}, {temp_alerts}]
                    }}]
                }}
            }});
        </script>

    </body>
    </html>
    """
