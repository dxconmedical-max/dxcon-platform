from flask import Blueprint, request, redirect

from app.extensions.db import db
from app.models.test_result import TestResult
from app.models.order_item import OrderItem
from app.models.test_catalog import TestCatalog


test_results_web_bp = Blueprint("test_results_web", __name__)


@test_results_web_bp.route("/results")
def results_page():

    results = TestResult.query.all()

    rows = ""

    for result in results:
        rows += f"""
        <tr>
            <td>{result.test_name}</td>
            <td>{result.result_value}</td>
            <td>{result.unit or ""}</td>
            <td>{result.reference_range or ""}</td>
            <td>{result.interpretation or ""}</td>
        </tr>
        """

    return f"""
    <html>
    <body style="font-family:Arial;background:#f1f5f9;padding:30px;">

        <h1>Test Results</h1>

        <a href="/results/new"
           style="background:#0d6efd;color:white;padding:10px 15px;text-decoration:none;border-radius:6px;">
           + New Result
        </a>

        <br><br>

        <table border="1" cellpadding="10" style="background:white;width:100%;">
            <tr>
                <th>Test Name</th>
                <th>Result Value</th>
                <th>Unit</th>
                <th>Reference Range</th>
                <th>Interpretation</th>
            </tr>
            {rows}
        </table>

        <br>
        <a href="/dashboard">Back to Dashboard</a>

    </body>
    </html>
    """


@test_results_web_bp.route("/results/new", methods=["GET", "POST"])
def new_result():

    order_items = OrderItem.query.all()

    if request.method == "POST":

        order_item_id = request.form.get("order_item_id")

        order_item = OrderItem.query.get(order_item_id)
        test_name = request.form.get("test_name")

        if order_item:
            test = TestCatalog.query.get(order_item.test_catalog_id)
            if test:
                test_name = test.name

        result = TestResult(
            order_item_id=order_item_id,
            test_name=test_name,
            result_value=request.form.get("result_value"),
            unit=request.form.get("unit"),
            reference_range=request.form.get("reference_range"),
            interpretation=request.form.get("interpretation")
        )

        db.session.add(result)
        db.session.commit()

        return redirect("/results")

    item_options = ""

    for item in order_items:
        test = TestCatalog.query.get(item.test_catalog_id)
        test_name = test.name if test else item.test_catalog_id

        item_options += f"""
        <option value="{item.id}">
            {test_name}
        </option>
        """

    return f"""
    <html>
    <body style="font-family:Arial;background:#f1f5f9;padding:30px;">

        <h1>New Test Result</h1>

        <form method="POST">
            <label>Order Item</label><br>
            <select name="order_item_id">
                {item_options}
            </select><br><br>

            <input name="test_name" placeholder="Test Name fallback"><br><br>

            <input name="result_value" placeholder="Result Value"><br><br>

            <input name="unit" placeholder="Unit"><br><br>

            <input name="reference_range" placeholder="Reference Range"><br><br>

            <textarea name="interpretation" placeholder="Interpretation"></textarea><br><br>

            <button type="submit">Save Result</button>
        </form>

        <br>
        <a href="/results">Back to Results</a>

    </body>
    </html>
    """
