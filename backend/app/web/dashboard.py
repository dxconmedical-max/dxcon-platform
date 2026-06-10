from flask import Blueprint

from app.models.patient import Patient
from app.models.company import Company
from app.models.order import Order
from app.models.invoice import Invoice
from app.models.payment import Payment
from app.models.test_result import TestResult
from app.models.sample_tracking import SampleTracking
from app.models.transport_box import TransportBox
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

    box_count = TransportBox.query.count()
    temp_alerts = TransportBox.query.filter(
        TransportBox.alert_status != "NORMAL"
    ).count()

    revenue = sum(payment.amount or 0 for payment in Payment.query.all())

    return f"""
    <html>
    <head>
        <title>DxCon Control Hub</title>
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
                padding:11px 0;
                border-bottom:1px solid rgba(255,255,255,.15);
                font-size:14px;
            }}
            .content {{
                flex:1;
                padding:32px;
            }}
            .section-title {{
                margin-top:34px;
                margin-bottom:16px;
                color:#0a4b5c;
            }}
            .cards {{
                display:grid;
                grid-template-columns:repeat(4,1fr);
                gap:18px;
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
        </style>
    </head>

    <body>
        <div class="layout">
            <div class="sidebar">
                <h2>DxCon</h2>

                <div class="menu">
                    <a href="/dashboard">Dashboard</a>
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
                    <a href="/result-files">Result Files</a>
                    <a href="/invoices">Invoices</a>
                    <a href="/payments">Payments</a>
                    <a href="/logout">Logout</a>
                </div>
            </div>

            <div class="content">
                <h1>DxCon Operations Dashboard</h1>

                <h2 class="section-title">Business Operations</h2>

                <div class="cards">
                    <div class="card"><div class="label">Revenue</div><div class="value green">{revenue:,.0f} VND</div></div>
                    <div class="card"><div class="label">Patients</div><div class="value">{patient_count}</div></div>
                    <div class="card"><div class="label">Companies</div><div class="value">{company_count}</div></div>
                    <div class="card"><div class="label">Orders</div><div class="value">{order_count}</div></div>

                    <div class="card"><div class="label">Pending Orders</div><div class="value orange">{pending_orders}</div></div>
                    <div class="card"><div class="label">Completed Orders</div><div class="value green">{completed_orders}</div></div>
                    <div class="card"><div class="label">Invoices</div><div class="value">{invoice_count}</div></div>
                    <div class="card"><div class="label">Payments</div><div class="value">{payment_count}</div></div>

                    <div class="card"><div class="label">Unpaid Invoices</div><div class="value red">{unpaid_invoices}</div></div>
                    <div class="card"><div class="label">Paid Invoices</div><div class="value green">{paid_invoices}</div></div>
                    <div class="card"><div class="label">Pending Results</div><div class="value red">{pending_results}</div></div>
                    <div class="card"><div class="label">Approved Results</div><div class="value green">{approved_results}</div></div>
                </div>

                <h2 class="section-title">IoT & Logistics</h2>

                <div class="cards">
                    <div class="card"><div class="label">Total Samples</div><div class="value purple">{sample_count}</div></div>
                    <div class="card"><div class="label">Samples In Transit</div><div class="value orange">{in_transit_samples}</div></div>
                    <div class="card"><div class="label">Samples Received</div><div class="value">{received_samples}</div></div>
                    <div class="card"><div class="label">Samples Completed</div><div class="value green">{completed_samples}</div></div>

                    <div class="card"><div class="label">Transport Boxes</div><div class="value">{box_count}</div></div>
                    <div class="card"><div class="label">Temperature Alerts</div><div class="value red">{temp_alerts}</div></div>
                    <div class="card"><div class="label">Total Results</div><div class="value purple">{result_count}</div></div>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
