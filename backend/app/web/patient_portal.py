from flask import Blueprint, request

from app.models.patient import Patient
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.test_catalog import TestCatalog
from app.models.test_result import TestResult
from app.models.result_file import ResultFile


patient_portal_web_bp = Blueprint("patient_portal_web", __name__)


@patient_portal_web_bp.route("/portal", methods=["GET", "POST"])
def patient_portal():

    if request.method == "POST":

        patient_code = request.form.get("patient_code")
        phone = request.form.get("phone")

        patient = Patient.query.filter_by(
            patient_code=patient_code
        ).first()

        if not patient:
            return """
            <h2>Không tìm thấy thông tin</h2>
            <p>Vui lòng kiểm tra lại mã bệnh nhân.</p>
            <a href="/portal">Quay lại</a>
            """

        orders = Order.query.filter_by(patient_id=patient.id).all()

        order_blocks = ""

        for order in orders:

            items = OrderItem.query.filter_by(order_id=order.id).all()
            files = ResultFile.query.filter_by(order_id=order.id).all()

            result_rows = ""
            file_rows = ""

            for item in items:

                test = TestCatalog.query.get(item.test_catalog_id)
                result = TestResult.query.filter_by(order_item_id=item.id).first()

                test_name = test.name if test else ""
                result_value = result.result_value if result else ""
                unit = result.unit if result else ""
                reference = result.reference_range if result else ""
                flag = result.flag if result else ""

                result_rows += f"""
                <tr>
                    <td>{test_name}</td>
                    <td>{result_value}</td>
                    <td>{unit}</td>
                    <td>{reference}</td>
                    <td>{flag}</td>
                </tr>
                """

            for file in files:
                file_rows += f"""
                <li>
                    <a href="/result-files/download/{file.id}">
                        {file.file_name}
                    </a>
                </li>
                """

            order_blocks += f"""
            <div style="background:white;padding:20px;margin-bottom:20px;border-radius:10px;">
                <h3>Order: {order.order_code}</h3>
                <p>Status: {order.status}</p>

                <table border="1" cellpadding="10" style="width:100%;">
                    <tr>
                        <th>Test</th>
                        <th>Result</th>
                        <th>Unit</th>
                        <th>Reference</th>
                        <th>Flag</th>
                    </tr>
                    {result_rows}
                </table>

                <h4>Uploaded Result Files</h4>
                <ul>
                    {file_rows}
                </ul>

                <br>
                <a href="/results/report/{order.id}/pdf">
                    Download Generated PDF Report
                </a>
            </div>
            """

        return f"""
        <html>
        <body style="font-family:Arial;background:#f1f5f9;padding:30px;">

            <h1>DxCon Patient Portal</h1>

            <h2>{patient.full_name}</h2>
            <p>Patient Code: {patient.patient_code}</p>
            <p>Phone: {patient.phone}</p>

            {order_blocks}

            <a href="/portal">Tra cứu bệnh nhân khác</a>

        </body>
        </html>
        """

    return """
    <html>
    <body style="font-family:Arial;background:#f1f5f9;padding:40px;">

        <h1>DxCon Patient Portal</h1>

        <p>Tra cứu kết quả xét nghiệm</p>

        <form method="POST">
            <label>Mã bệnh nhân</label><br>
            <input name="patient_code" placeholder="PT001"><br><br>

            <label>Số điện thoại</label><br>
            <input name="phone" placeholder="0901234567"><br><br>

            <button type="submit">
                Tra cứu kết quả
            </button>
        </form>

    </body>
    </html>
    """
