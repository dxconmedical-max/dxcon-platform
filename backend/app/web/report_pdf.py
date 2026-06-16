import qrcode
from reportlab.lib.utils import ImageReader
def generate_verify_qr(result_id):

    verify_url = (
        f"http://172.20.10.2:8000/"
        f"results/verify/{result_id}"
    )

    qr = qrcode.make(verify_url)

    qr_path = f"/tmp/{result_id}.png"

    qr.save(qr_path)

    return qr_path
from flask import Blueprint, send_file

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from app.models.order import Order
from app.models.patient import Patient
from app.models.order_item import OrderItem
from app.models.test_catalog import TestCatalog
from app.models.test_result import TestResult
from app.models.clinical_summary import ClinicalSummary
from app.services.medical_summary import generate_medical_summary
from app.services.ai_risk_engine import analyze_profile

import os


report_pdf_web_bp = Blueprint(
    "report_pdf_web",
    __name__
)


def draw_wrapped_text(pdf, text, x, y, max_chars=95, line_height=14):

    text = str(text or "")

    while text:
        line = text[:max_chars]
        pdf.drawString(x, y, line)
        text = text[max_chars:]
        y -= line_height

    return y


@report_pdf_web_bp.route("/results/report/<order_id>/pdf")
def report_pdf(order_id):

    order = Order.query.get(order_id)

    if not order:
        return "Order not found"

    items = OrderItem.query.filter_by(order_id=order_id).all()

    results = []

    for item in items:
        result = TestResult.query.filter_by(
            order_item_id=item.id
        ).first()

        if result:
            results.append(result)

    if not results:
        return """
        <h2>No result found</h2>
        <p>This order does not have test results yet.</p>
        <a href="/orders">Back to Orders</a>
        """

    patient = Patient.query.get(order.patient_id)

    base_dir = os.getcwd()
    folder = os.path.join(base_dir, "generated_reports")
    os.makedirs(folder, exist_ok=True)

    file_path = os.path.join(
        folder,
        f"DxCon_Report_{order.order_code}.pdf"
    )

    pdf = canvas.Canvas(file_path, pagesize=A4)

    width, height = A4
    y = height - 50

    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawString(50, y, "DxCon Laboratory Report")
    y -= 35

    pdf.setFont("Helvetica", 11)
    pdf.drawString(50, y, f"Order Code: {order.order_code}")
    y -= 22

    if patient:
        pdf.drawString(50, y, f"Patient Code: {patient.patient_code}")
        y -= 18
        pdf.drawString(50, y, f"Patient Name: {patient.full_name}")
        y -= 18
        pdf.drawString(50, y, f"DOB: {patient.date_of_birth or ''}")
        y -= 18
        pdf.drawString(50, y, f"Gender: {patient.gender or ''}")
        y -= 18
        pdf.drawString(50, y, f"Phone: {patient.phone or ''}")
        y -= 28

    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(50, y, "Test Results")
    y -= 25

    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawString(50, y, "Test")
    pdf.drawString(180, y, "Result")
    pdf.drawString(260, y, "Unit")
    pdf.drawString(330, y, "Reference")
    pdf.drawString(450, y, "Flag")
    y -= 18

    pdf.setFont("Helvetica", 10)

    for item in items:

        test = TestCatalog.query.get(item.test_catalog_id)

        result = TestResult.query.filter_by(
            order_item_id=item.id
        ).first()

        if not result:
            continue

        test_name = test.name if test else result.test_name

        pdf.drawString(50, y, str(test_name or "")[:22])
        pdf.drawString(180, y, str(result.result_value or ""))
        pdf.drawString(260, y, str(result.unit or ""))
        pdf.drawString(330, y, str(result.reference_range or ""))
        pdf.drawString(450, y, str(result.flag or ""))

        y -= 20

        if y < 100:
            pdf.showPage()
            y = height - 50

    y -= 15

    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(50, y, "AI Interpretation")
    y -= 22

    pdf.setFont("Helvetica", 10)

    for result in results:

        pdf.setFont("Helvetica-Bold", 10)
        pdf.drawString(50, y, f"{result.test_name}:")
        y -= 15

        pdf.setFont("Helvetica", 10)
        y = draw_wrapped_text(
            pdf,
            result.interpretation or "No interpretation available.",
            70,
            y,
            max_chars=95,
            line_height=14
        )

        y -= 14

        if y < 100:
            pdf.showPage()
            y = height - 50

    summary = generate_medical_summary(results)

    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(50, y, "Medical Summary")
    y -= 20

    pdf.setFont("Helvetica", 10)
    y = draw_wrapped_text(
        pdf,
        summary,
        70,
        y,
        max_chars=95,
        line_height=14
    )

    y -= 20

    clinical_summary = ClinicalSummary.query.filter_by(
        order_id=order.id
    ).first()

    if clinical_summary:

        if y < 160:
            pdf.showPage()
            y = height - 50

        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(50, y, "Clinical Summary")
        y -= 22

        pdf.setFont("Helvetica", 10)
        pdf.drawString(50, y, f"Risk Level: {clinical_summary.risk_level}")
        y -= 18

        pdf.drawString(50, y, "Findings:")
        y -= 16

        y = draw_wrapped_text(
            pdf,
            clinical_summary.findings or "",
            70,
            y,
            max_chars=95,
            line_height=14
        )

        y -= 10

        pdf.drawString(50, y, "Recommendations:")
        y -= 16

        y = draw_wrapped_text(
            pdf,
            clinical_summary.recommendations or "",
            70,
            y,
            max_chars=95,
            line_height=14
        )

        y -= 20

    if y < 100:
        pdf.showPage()
        y = height - 50

    risk_report = analyze_profile(results)

    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(50, y, "AI Risk Assessment")
    y -= 25

    pdf.setFont("Helvetica", 10)
    pdf.drawString(50, y, f"Risk Level: {risk_report['risk_level']}")
    y -= 20

    pdf.drawString(50, y, "Findings:")
    y -= 18

    findings = risk_report.get("findings") or ["No major risk finding"]

    for item in findings:
        pdf.drawString(70, y, f"- {item}")
        y -= 15

    y -= 5

    pdf.drawString(50, y, "Recommendations:")
    y -= 18

    recommendations = risk_report.get("recommendations") or [
        "Continue routine follow-up"
    ]

    for item in recommendations:
        pdf.drawString(70, y, f"- {item}")
        y -= 15

    y -= 20

    if y < 120:
        pdf.showPage()
        y = height - 50

    first_result = results[0]

    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawString(50, y, "Doctor Electronic Signature")
    y -= 20

    pdf.setFont("Helvetica", 10)
    pdf.drawString(50, y, f"Doctor: {first_result.approved_by or ''}")
    y -= 15
    pdf.drawString(50, y, f"License: {first_result.doctor_license or ''}")
    y -= 15
    pdf.drawString(50, y, f"Signed At: {first_result.approved_at or ''}")
    y -= 15
    pdf.drawString(50, y, f"Signature ID: {first_result.signature_id or ''}")
    y -= 25
    verify_url = (
        f"http://172.20.10.2:8000/"
        f"results/verify/{first_result.id}"
    )

    pdf.drawString(
        50,
        y,
        "Verification URL:"
    )

    y -= 15

    pdf.drawString(
        50,
        y,
        verify_url
    )

    y -= 80

    qr_path = generate_verify_qr(
        first_result.id
    )

    pdf.drawImage(
        ImageReader(qr_path),
        50,
        y,
        width=90,
        height=90
    )

    pdf.drawString(
        160,
        y + 45,
        "Scan QR to verify report"
    )
    
    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawString(50, y, "DxCon Laboratory System")

    pdf.save()

    return send_file(
        file_path,
        as_attachment=True,
        download_name=f"DxCon_Report_{order.order_code}.pdf"
    )
