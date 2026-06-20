from flask import Blueprint
from datetime import datetime

from app.models.user import User
from app.models.patient import Patient
from app.models.order import Order
from app.models.sample_tracking import SampleTracking
from app.models.test_result import TestResult
from app.models.invoice import Invoice
from app.models.payment import Payment
from app.models.audit_log import AuditLog


monitor_web_bp = Blueprint("monitor_web", __name__)


@monitor_web_bp.route("/monitor")
def monitor():

    return f"""
    <html>
    <body style="font-family:Arial;background:#f1f5f9;padding:30px;">
        <h1>DxCon Production Monitor</h1>
        <p><b>Checked at:</b> {datetime.utcnow()}</p>

        <div style="display:flex;gap:15px;flex-wrap:wrap;">
            <div class="card"><h3>Users</h3><h1>{User.query.count()}</h1></div>
            <div class="card"><h3>Patients</h3><h1>{Patient.query.count()}</h1></div>
            <div class="card"><h3>Orders</h3><h1>{Order.query.count()}</h1></div>
            <div class="card"><h3>Samples</h3><h1>{SampleTracking.query.count()}</h1></div>
            <div class="card"><h3>Results</h3><h1>{TestResult.query.count()}</h1></div>
            <div class="card"><h3>Invoices</h3><h1>{Invoice.query.count()}</h1></div>
            <div class="card"><h3>Payments</h3><h1>{Payment.query.count()}</h1></div>
            <div class="card"><h3>Audit Logs</h3><h1>{AuditLog.query.count()}</h1></div>
        </div>

        <br>
        <div class="panel">
            <h2>Production Links</h2>
            <a href="/api/v1/system/health">System Health</a><br>
            <a href="/api/v1/system/stats">System Stats</a><br>
            <a href="/api/v1/system/routes">System Routes</a><br>
            <a href="/api/v1/system/backup-status">Backup Status</a><br>
            <a href="/audit">Audit Center</a><br>
            <a href="/security">Security Center</a><br>
            <a href="/executive-v9">Executive Dashboard</a><br>
            <a href="/finance">Finance</a><br>
            <a href="/crm-pipeline">CRM Pipeline</a><br>
            <a href="/logistics">Logistics</a>
        </div>

        <style>
            .card {{
                background:white;
                padding:20px;
                border-radius:12px;
                width:200px;
                box-shadow:0 4px 12px rgba(0,0,0,.08);
            }}
            .panel {{
                background:white;
                padding:20px;
                border-radius:12px;
                box-shadow:0 4px 12px rgba(0,0,0,.08);
            }}
            a {{
                line-height:2;
            }}
        </style>
    </body>
    </html>
    """
