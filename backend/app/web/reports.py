from flask import Blueprint

from app.models.order import Order
from app.models.patient import Patient
from app.models.order_item import OrderItem
from app.models.test_catalog import TestCatalog
from app.models.test_result import TestResult


reports_web_bp = Blueprint(
    "reports_web",
    __name__
)


@reports_web_bp.route("/results/report/<order_id>")
def report_page(order_id):

    order = Order.query.get(order_id)

    if not order:
        return "Order not found"

    patient = Patient.query.get(order.patient_id)

    items = OrderItem.query.filter_by(
        order_id=order_id
    ).all()

    rows = ""

    for item in items:

        test = TestCatalog.query.get(
            item.test_catalog_id
        )

        result = TestResult.query.filter_by(
            order_item_id=item.id
        ).first()

        test_name = ""
        result_value = ""
        unit = ""
        reference = ""
        flag = ""

        if test:
            test_name = test.name

        if result:
            result_value = result.result_value
            unit = result.unit
            reference = result.reference_range
            flag = result.flag

        rows += f"""
        <tr>
            <td>{test_name}</td>
            <td>{result_value}</td>
            <td>{unit}</td>
            <td>{reference}</td>
            <td>{flag}</td>
        </tr>
        """

    return f"""
    <html>
    <body style="
        font-family:Arial;
        background:#f8fafc;
        padding:40px;
    ">

        <h1>DxCon Laboratory Report</h1>

        <hr>

        <h3>Patient Information</h3>

        <p>
            <strong>Patient Code:</strong>
            {patient.patient_code if patient else ""}
        </p>

        <p>
            <strong>Name:</strong>
            {patient.full_name if patient else ""}
        </p>

        <p>
            <strong>DOB:</strong>
            {patient.date_of_birth if patient else ""}
        </p>

        <p>
            <strong>Gender:</strong>
            {patient.gender if patient else ""}
        </p>

        <p>
            <strong>Phone:</strong>
            {patient.phone if patient else ""}
        </p>

        <hr>

        <h3>Test Results</h3>

        <table border="1"
               cellpadding="10"
               style="width:100%;background:white;">

            <tr>
                <th>Test</th>
                <th>Result</th>
                <th>Unit</th>
                <th>Reference</th>
                <th>Flag</th>
            </tr>

            {rows}

        </table>

        <br>
        <a href="/results/report/{order.id}/pdf">
    Download PDF
</a>

<br><br>
        <a href="/orders">
            Back to Orders
        </a>

    </body>
    </html>
    """
