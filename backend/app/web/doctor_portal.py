from flask import Blueprint, redirect

from app.extensions.db import db
from app.models.test_result import TestResult
from app.models.order_item import OrderItem
from app.models.order import Order
from app.models.patient import Patient
from app.models.result_file import ResultFile
from app.utils.auth import role_required


doctor_portal_web_bp = Blueprint("doctor_portal_web", __name__)


@doctor_portal_web_bp.route("/doctor")
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
            <td>{file_links}</td>
            <td>
                <a href="/doctor/approve/{result.id}">Approve</a>
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
    db.session.commit()

    return redirect("/doctor")
