from flask import Blueprint, request, redirect

from app.extensions.db import db
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.test_catalog import TestCatalog
from app.services.pricing import get_price_for_test


order_items_web_bp = Blueprint("order_items_web", __name__)


@order_items_web_bp.route("/orders/<order_id>/items")
def order_items_page(order_id):

    order = Order.query.get(order_id)

    if not order:
        return "Order not found"

    items = OrderItem.query.filter_by(order_id=order_id).all()

    rows = ""
    total_amount = 0

    for item in items:
        test = TestCatalog.query.get(item.test_catalog_id)
        price = item.price or 0
        total_amount += price

        rows += f"""
        <tr>
            <td>{test.name if test else ""}</td>
            <td>{price:,.0f} VND</td>
        </tr>
        """

    order.total_amount = total_amount
    db.session.commit()

    return f"""
    <html>
    <body style="font-family:Arial;background:#f1f5f9;padding:30px;">
        <h1>Order Items - {order.order_code}</h1>

        <p><strong>Contract ID:</strong> {order.contract_id or "No Contract"}</p>

        <a href="/orders/{order.id}/items/new"
           style="background:#0d6efd;color:white;padding:10px 15px;text-decoration:none;border-radius:6px;">
           + Add Test
        </a>

        <br><br>

        <table border="1" cellpadding="10" style="background:white;width:100%;">
            <tr>
                <th>Test</th>
                <th>Price</th>
            </tr>
            {rows}
        </table>

        <br>

        <h3>Order Summary</h3>
        <p><strong>Total Tests:</strong> {len(items)}</p>
        <p><strong>Total Amount:</strong> {total_amount:,.0f} VND</p>

        <br>
        <a href="/orders">Back to Orders</a>
    </body>
    </html>
    """


@order_items_web_bp.route("/orders/<order_id>/items/new", methods=["GET", "POST"])
def new_order_item(order_id):

    order = Order.query.get(order_id)

    if not order:
        return "Order not found"

    tests = TestCatalog.query.all()

    if request.method == "POST":

        test_catalog_id = request.form.get("test_catalog_id")

        pricing = get_price_for_test(
            test_catalog_id,
            order.contract_id
        )

        if pricing.get("error"):
            return pricing.get("error")

        item = OrderItem(
            order_id=order.id,
            test_catalog_id=test_catalog_id,
            price=pricing.get("final_price", 0)
        )

        db.session.add(item)
        db.session.commit()

        return redirect(f"/orders/{order.id}/items")

    test_options = ""

    for test in tests:
        test_options += f"""
        <option value="{test.id}">
            {test.code} - {test.name} - Standard {test.price:,.0f} VND
        </option>
        """

    return f"""
    <html>
    <body style="font-family:Arial;background:#f1f5f9;padding:30px;">
        <h1>Add Test To Order - {order.order_code}</h1>

        <p><strong>Contract Pricing:</strong> {order.contract_id or "No Contract"}</p>

        <form method="POST">
            <label>Test</label><br>
            <select name="test_catalog_id">
                {test_options}
            </select>

            <br><br>

            <button type="submit">Add Test</button>
        </form>

        <br>
        <a href="/orders/{order.id}/items">Back</a>
    </body>
    </html>
    """
