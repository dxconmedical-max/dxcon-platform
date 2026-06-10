from flask import Blueprint, send_file

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from app.models.order import Order
from app.models.patient import Patient
from app.models.order_item import OrderItem
from app.models.test_catalog import TestCatalog
from app.models.test_result import TestResult

import os


report_pdf_web_bp = Blueprint("report_pdf_web", __name__)


@report_pdf_web_bp.route("/results/report/<order_id>/pdf")
def report_pdf(order_id):

    order = Order.query.get(order_id)

    if not order:
        return "Order not found"

    items = OrderItem.query.filter_by(order_id=order_id).all()

    results = []

    for item in items:
        result = TestResult.query.filter_by(order_item_id=item.id).first()

        if result:
            results.append(result)

    if not results:
        return """
        <h2>No result found</h2>
        <p>This order does not have test results yet.</p>
        <a href="/orders">Back to Orders</a>
        """

    for result in results:
        if result.approval_status != "APPROVED":
            return """
            <h2>Result not approved</h2>
            <p>Doctor approval required before PDF download.</p>
            <a href="/doctor">Go to Doctor Portal</a>
            """

    patient = Patient.query.get(order.patient_id)

    base_dir = os.getcwd()
    folder = os.path.join(base_dir, "generated_reports")
    os.makedirs(folder, exist_ok=True)

    file_path = os.path.join(folder, f"DxCon_Report_{order.order_code}.pdf")

    pdf = canvas.Canvas(file_path, pagesize=A4)

    width, height = A4
    y = height - 50

    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawString(50, y, "DxCon Laboratory Report")
    y -= 40

    pdf.setFont("Helvetica", 11)
    pdf.drawString(50, y, f"Order Code: {order.order_code}")
    y -= 20

    if patient:
        pdf.drawString(50, y, f"Patient Code: {patient.patient_code}")
        y -= 20
        pdf.drawString(50, y, f"Patient Name: {patient.full_name}")
        y -= 20
        pdf.drawString(50, y, f"DOB: {patient.date_of_birth or ''}")
        y -= 20
        pdf.drawString(50, y, f"Gender: {patient.gender or ''}")
        y -= 20
        pdf.drawString(50, y, f"Phone: {patient.phone or ''}")
        y -= 30

    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(50, y, "Test Results")
    y -= 25

    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawString(50, y, "Test")
    pdf.drawString(180, y, "Result")
    pdf.drawString(260, y, "Unit")
    pdf.drawString(330, y, "Reference")
    pdf.drawString(450, y, "Flag")
    y -= 15

    pdf.setFont("Helvetica", 10)

    for item in items:

        test = TestCatalog.query.get(item.test_catalog_id)
        result = TestResult.query.filter_by(order_item_id=item.id).first()

        test_name = test.name if test else ""
        result_value = result.result_value if result else ""
        unit = result.unit if result else ""
        reference = result.reference_range if result else ""
        flag = result.flag if result else ""

        pdf.drawString(50, y, test_name[:22])
        pdf.drawString(180, y, str(result_value))
        pdf.drawString(260, y, str(unit))
        pdf.drawString(330, y, str(reference))
        pdf.drawString(450, y, str(flag))

        y -= 20

        if y < 80:
            pdf.showPage()
            y = height - 50

    pdf.save()

    return send_file(
        file_path,
        as_attachment=True,
        download_name=f"DxCon_Report_{order.order_code}.pdf"
    )
