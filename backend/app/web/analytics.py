from flask import Blueprint

from app.models.payment import Payment
from app.models.order import Order
from app.models.invoice import Invoice
from app.models.sample_tracking import SampleTracking
from app.models.transport_box import TransportBox
from app.models.test_result import TestResult
from app.models.alert import Alert
from app.utils.auth import role_required


analytics_web_bp = Blueprint("analytics_web", __name__)


@analytics_web_bp.route("/analytics")
@role_required("SUPER_ADMIN")
def analytics():

    payments = Payment.query.all()
    orders = Order.query.all()
    samples = SampleTracking.query.all()
    boxes = TransportBox.query.all()
    results = TestResult.query.all()

    total_revenue = sum(payment.amount or 0 for payment in payments)

    order_count = len(orders)
    pending_orders = Order.query.filter_by(status="PENDING").count()
    processing_orders = Order.query.filter_by(status="PROCESSING").count()
    completed_orders = Order.query.filter_by(status="COMPLETED").count()

    paid_invoices = Invoice.query.filter_by(payment_status="PAID").count()
    unpaid_invoices = Invoice.query.filter_by(payment_status="UNPAID").count()

    checked_in_samples = SampleTracking.query.filter_by(status="CHECKED_IN").count()
    received_samples = SampleTracking.query.filter_by(status="RECEIVED").count()
    in_transit_samples = SampleTracking.query.filter_by(status="IN_TRANSIT").count()
    completed_samples = SampleTracking.query.filter_by(status="COMPLETED").count()

    normal_boxes = TransportBox.query.filter_by(alert_status="NORMAL").count()
    alert_boxes = TransportBox.query.filter(
        TransportBox.alert_status != "NORMAL"
    ).count()

    approved_results = TestResult.query.filter_by(approval_status="APPROVED").count()
    pending_results = TestResult.query.filter_by(approval_status="PENDING").count()

    open_alerts = Alert.query.filter_by(status="OPEN").count()

    approval_rate = 0
    if len(results) > 0:
        approval_rate = round(approved_results / len(results) * 100, 1)

    sample_completion_rate = 0
    if len(samples) > 0:
        sample_completion_rate = round(completed_samples / len(samples) * 100, 1)

    avg_order_value = 0
    if order_count > 0:
        avg_order_value = round(total_revenue / order_count, 0)

    return f"""
    <html>
    <head>
        <title>DxCon Executive Analytics</title>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
            body {{
                font-family:Arial;
                background:#f1f5f9;
                padding:30px;
                color:#0f172a;
            }}
            .cards {{
                display:grid;
                grid-template-columns:repeat(4,1fr);
                gap:18px;
                margin-bottom:30px;
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
            }}
            .chart-box {{
                background:white;
                padding:22px;
                border-radius:14px;
                box-shadow:0 4px 12px rgba(0,0,0,.08);
            }}
            canvas {{
                width:100% !important;
                height:280px !important;
            }}
            a {{
                color:#0d6efd;
                text-decoration:none;
            }}
        </style>
    </head>

    <body>

        <h1>DxCon Executive Analytics</h1>

        <div class="cards">
            <div class="card">
                <div class="label">Total Revenue</div>
                <div class="value green">{total_revenue:,.0f} VND</div>
            </div>

            <div class="card">
                <div class="label">Average Order Value</div>
                <div class="value">{avg_order_value:,.0f} VND</div>
            </div>

            <div class="card">
                <div class="label">Doctor Approval Rate</div>
                <div class="value purple">{approval_rate}%</div>
            </div>

            <div class="card">
                <div class="label">Open Alerts</div>
                <div class="value red">{open_alerts}</div>
            </div>
        </div>

        <div class="cards">
            <div class="card">
                <div class="label">Orders</div>
                <div class="value">{order_count}</div>
            </div>

            <div class="card">
                <div class="label">Samples</div>
                <div class="value purple">{len(samples)}</div>
            </div>

            <div class="card">
                <div class="label">Sample Completion Rate</div>
                <div class="value green">{sample_completion_rate}%</div>
            </div>

            <div class="card">
                <div class="label">Temperature Alerts</div>
                <div class="value red">{alert_boxes}</div>
            </div>
        </div>

        <div class="charts">

            <div class="chart-box">
                <h2>Orders by Status</h2>
                <canvas id="ordersChart"></canvas>
            </div>

            <div class="chart-box">
                <h2>Invoice Status</h2>
                <canvas id="invoiceChart"></canvas>
            </div>

            <div class="chart-box">
                <h2>Sample Logistics</h2>
                <canvas id="sampleChart"></canvas>
            </div>

            <div class="chart-box">
                <h2>Transport Box Alerts</h2>
                <canvas id="boxChart"></canvas>
            </div>

            <div class="chart-box">
                <h2>Result Approval</h2>
                <canvas id="resultChart"></canvas>
            </div>

            <div class="chart-box">
                <h2>Revenue Snapshot</h2>
                <canvas id="revenueChart"></canvas>
            </div>

        </div>

        <br>
        <a href="/dashboard">Back to Dashboard</a>
        |
        <a href="/operations">Operations Tower</a>
        |
        <a href="/collector-kpi">Collector KPI</a>
        |
        <a href="/tat-kpi">TAT KPI</a>

        <script>
            new Chart(document.getElementById('ordersChart'), {{
                type: 'bar',
                data: {{
                    labels: ['Pending', 'Processing', 'Completed'],
                    datasets: [{{
                        label: 'Orders',
                        data: [{pending_orders}, {processing_orders}, {completed_orders}]
                    }}]
                }}
            }});

            new Chart(document.getElementById('invoiceChart'), {{
                type: 'doughnut',
                data: {{
                    labels: ['Paid', 'Unpaid'],
                    datasets: [{{
                        label: 'Invoices',
                        data: [{paid_invoices}, {unpaid_invoices}]
                    }}]
                }}
            }});

            new Chart(document.getElementById('sampleChart'), {{
                type: 'bar',
                data: {{
                    labels: ['Checked In', 'Received', 'In Transit', 'Completed'],
                    datasets: [{{
                        label: 'Samples',
                        data: [{checked_in_samples}, {received_samples}, {in_transit_samples}, {completed_samples}]
                    }}]
                }}
            }});

            new Chart(document.getElementById('boxChart'), {{
                type: 'doughnut',
                data: {{
                    labels: ['Normal', 'Alert'],
                    datasets: [{{
                        label: 'Transport Boxes',
                        data: [{normal_boxes}, {alert_boxes}]
                    }}]
                }}
            }});

            new Chart(document.getElementById('resultChart'), {{
                type: 'bar',
                data: {{
                    labels: ['Approved', 'Pending'],
                    datasets: [{{
                        label: 'Results',
                        data: [{approved_results}, {pending_results}]
                    }}]
                }}
            }});

            new Chart(document.getElementById('revenueChart'), {{
                type: 'bar',
                data: {{
                    labels: ['Revenue', 'Avg Order'],
                    datasets: [{{
                        label: 'VND',
                        data: [{total_revenue}, {avg_order_value}]
                    }}]
                }}
            }});
        </script>

    </body>
    </html>
    """
