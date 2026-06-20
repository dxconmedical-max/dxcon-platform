
from flask import Blueprint

from app.models.patient import Patient
from app.models.order import Order
from app.models.driver import Driver
from app.models.sample_tracking import SampleTracking
from app.models.home_collection import HomeCollection
from app.models.test_result import TestResult
from app.models.invoice import Invoice
from app.models.payment import Payment
from app.models.contract import Contract
from app.models.clinical_summary import ClinicalSummary
from app.core.web_authz import web_roles_required

executive_v9_bp = Blueprint("executive_v9", __name__)


@executive_v9_bp.route("/executive-v9")
@web_roles_required("SUPER_ADMIN", "ADMIN")
def executive_v9():

    revenue = sum([(p.amount or 0) for p in Payment.query.all()])
    invoice_total = sum([(i.total_amount or 0) for i in Invoice.query.all()])

    pending_results = TestResult.query.filter_by(approval_status="PENDING").count()
    approved_results = TestResult.query.filter_by(approval_status="APPROVED").count()

    in_transit = SampleTracking.query.filter_by(status="IN_TRANSIT").count()
    completed_samples = SampleTracking.query.filter_by(status="COMPLETED").count()

    high_risk = ClinicalSummary.query.filter_by(risk_level="HIGH").count()
    critical_risk = ClinicalSummary.query.filter_by(risk_level="CRITICAL").count()

    return f"""
    <html>
    <body style="font-family:Arial;background:#f1f5f9;padding:30px;">
        <h1>DxCon Executive Command Center V9</h1>

        <div style="display:flex;gap:15px;flex-wrap:wrap;">
            <div class="card"><h3>Patients</h3><h1>{Patient.query.count()}</h1></div>
            <div class="card"><h3>Orders</h3><h1>{Order.query.count()}</h1></div>
            <div class="card"><h3>Bookings</h3><h1>{HomeCollection.query.count()}</h1></div>
            <div class="card"><h3>Samples</h3><h1>{SampleTracking.query.count()}</h1></div>
            <div class="card"><h3>Collectors</h3><h1>{Driver.query.count()}</h1></div>
            <div class="card"><h3>Contracts</h3><h1>{Contract.query.count()}</h1></div>
            <div class="card"><h3>Revenue</h3><h1>{revenue:,.0f}</h1></div>
            <div class="card"><h3>Invoice Total</h3><h1>{invoice_total:,.0f}</h1></div>
        </div>

        <h2>Operations</h2>
        <div style="display:flex;gap:15px;flex-wrap:wrap;">
            <div class="card"><h3>In Transit</h3><h1>{in_transit}</h1></div>
            <div class="card"><h3>Completed Samples</h3><h1>{completed_samples}</h1></div>
            <div class="card"><h3>Pending Results</h3><h1>{pending_results}</h1></div>
            <div class="card"><h3>Approved Results</h3><h1>{approved_results}</h1></div>
        </div>

        <h2>AI Risk</h2>
        <div style="display:flex;gap:15px;flex-wrap:wrap;">
            <div class="card"><h3>High Risk</h3><h1>{high_risk}</h1></div>
            <div class="card"><h3>Critical Risk</h3><h1>{critical_risk}</h1></div>
        </div>

        <br>
        <a href="/finance">Finance</a> |
        <a href="/crm-pipeline">CRM Pipeline</a> |
        <a href="/logistics">Logistics</a> |
        <a href="/doctor-workbench">Doctor</a>

        <style>
            .card {{
                background:white;
                padding:20px;
                border-radius:12px;
                width:220px;
                box-shadow:0 4px 12px rgba(0,0,0,.08);
            }}
        </style>
    </body>
    </html>
    """
