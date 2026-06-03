from flask import Blueprint, request

from app.extensions.db import db
from app.models.order import Order

orders_bp = Blueprint(
    "orders",
    __name__,
    url_prefix="/api/v1/orders"
)


@orders_bp.route("", methods=["GET"])
def get_orders():

    orders = Order.query.all()

    return {
        "count": len(orders),
        "orders": [
            order.to_dict()
            for order in orders
        ]
    }


@orders_bp.route("", methods=["POST"])
def create_order():

    data = request.get_json()

    order = Order(
        order_code=data.get("order_code"),
        patient_id=data.get("patient_id"),
        laboratory_id=data.get("laboratory_id"),
        total_amount=data.get("total_amount", 0)
    )

    db.session.add(order)
    db.session.commit()

    return {
        "message": "Order created",
        "order": order.to_dict()
    }, 201
