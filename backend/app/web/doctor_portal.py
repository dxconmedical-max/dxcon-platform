from flask import Blueprint, redirect
from datetime import datetime
import uuid

from app.extensions.db import db
from app.models.test_result import TestResult
from app.models.order_item import OrderItem
from app.models.order import Order
from app.models.patient import Patient
from app.models.result_file import ResultFile
from app.models.audit_log import AuditLog
from app.models.alert import Alert
from app.models.sample_tracking import SampleTracking
from app.models.clinical_summary import ClinicalSummary
from app.services.event_logger import create_event
from app.services.ai_summary import build_summary
from app.utils.auth import role_required


doctor_portal_web_bp = Blueprint("doctor_portal_web", __name__)


@doctor_portal_web_bp.route("/legacy/doctor")
@role_required("SUPER_ADMIN", "DOCTOR")
def doctor_dashboard():

    results = TestResult.query.all()
    rows = ""

    for result in results:

        order_item = OrderItem.query.get(result.order_item_id)
        order = Order.query.get(order_item.order_id) if order_item else None
        patient = Patient.query.get(order.patient_id) if order else None

        patient_name = patient.full_name if patient else ""
        order_code = order.order_code if order else ""

        file_links = ""

        if order:
            files = ResultFile.query.filter_by(order_id=order.id).all()

            for file in files:
                file_links += f"""
                <a href="/result-files/download/{file.id}">
                    {file.file_name}
                </a><br>
                """

        signed_info = ""

        if result.approved_by:
            signed_info = f"""
            <strong>{result.approved_by}</strong><br>
            License: {result.doctor_license or ""}<br>
            Signed: {result.approved_at or ""}<br>
            Signature: {result.signature_id or ""}
            """

        rows += f"""
        <tr>
            <td>{patient_name}</td>
            <td>{order_code}</td>
            <td>{result.test_name}</td>
            <td>{result.result_value}</td>
            <td>{result.unit or ""}</td>
            <td>{result.reference_range or ""}</td>
            <td>{result.flag or ""}</td>
            <td>{result.approval_status}</td>
            <td>{signed_info}</td>
            <td>{file_links}</td>
            <td>
                <a href="/doctor/approve/{result.id}">
                    Approve + e-Sign
                </a>
            </td>
        </tr>
        """

    return f"""
    <html>
    <body style="font-family:Arial;background:#f1f5f9;padding:30px;">

        <h1>Doctor Portal</h1>

        <table border="1" cellpadding="10" style="background:white;width:100%;">
            <tr>
                <th>Patient</th>
                <th>Order</th>
                <th>Test</th>
                <th>Result</th>
                <th>Unit</th>
                <th>Reference</th>
                <th>Flag</th>
                <th>Status</th>
                <th>e-Signature</th>
                <th>Uploaded Files</th>
                <th>Action</th>
            </tr>
            {rows}
        </table>

        <br>
        <a href="/dashboard">Back to Dashboard</a>

    </body>
    </html>
    """


@doctor_portal_web_bp.route("/doctor/approve/<result_id>")
@role_required("SUPER_ADMIN", "DOCTOR")
def approve_result(result_id):

    result = TestResult.query.get(result_id)

    if not result:
        return "Result not found"

    result.approval_status = "APPROVED"
    result.approved_by = "Dr. DxCon Medical Director"
    result.doctor_license = "VN-MED-000001"
    result.approved_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    result.signature_id = "SIG-" + str(uuid.uuid4())[:8].upper()

    db.session.commit()

    order_item = OrderItem.query.get(result.order_item_id)
    order = Order.query.get(order_item.order_id) if order_item else None

    if order:
        order_items = OrderItem.query.filter_by(order_id=order.id).all()

        order_results = []

        for item in order_items:
            item_result = TestResult.query.filter_by(
                order_item_id=item.id
            ).first()

            if item_result:
                order_results.append(item_result)

        summary_data = build_summary(order_results)

        existing_summary = ClinicalSummary.query.filter_by(
            order_id=order.id
        ).first()

        if not existing_summary:
            existing_summary = ClinicalSummary(
                order_id=order.id
            )
            db.session.add(existing_summary)

        existing_summary.risk_level = summary_data["risk_level"]
        existing_summary.findings = summary_data["findings"]
        existing_summary.recommendations = summary_data["recommendations"]

        db.session.commit()

    audit = AuditLog(
        user_email="doctor@dxcon.vn",
        action="APPROVE_AND_ESIGN_RESULT",
        object_type="TestResult",
        object_id=result.id,
        ip_address="127.0.0.1"
    )

    db.session.add(audit)
    db.session.commit()

    alert = Alert(
        title="Result Approved",
        message=f"{result.test_name} approved and e-signed by doctor",
        status="OPEN"
    )

    db.session.add(alert)
    db.session.commit()

    sample = SampleTracking.query.first()

    if sample:
        create_event(
            sample.id,
            "DOCTOR_APPROVED",
            f"{result.test_name} approved and e-signed"
        )

    return redirect("/legacy/doctor")
