from app.extensions.db import db
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.test_result import TestResult


def update_order_status(order_id):

    items = OrderItem.query.filter_by(
        order_id=order_id
    ).all()

    if not items:
        return

    total_tests = len(items)
    total_results = 0

    for item in items:

        result = TestResult.query.filter_by(
            order_item_id=item.id
        ).first()

        if result:
            total_results += 1

    order = Order.query.get(order_id)

    if not order:
        return

    if total_results == 0:
        order.status = "PENDING"

    elif total_results < total_tests:
        order.status = "PROCESSING"

    else:
        order.status = "COMPLETED"

    db.session.commit()
