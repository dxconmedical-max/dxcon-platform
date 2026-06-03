from flask import Blueprint, request

from app.extensions.db import db
from app.models.order_item import OrderItem
from app.services.pricing import get_price_for_test


order_items_bp = Blueprint(
    "order_items",
    __name__,
    url_prefix="/api/v1/order-items"
)


@order_items_bp.route("", methods=["GET"])
def get_order_items():

    items = OrderItem.query.all()

    return {
        "count": len(items),
        "items": [
            item.to_dict()
            for item in items
        ]
    }


@order_items_bp.route("", methods=["POST"])
def create_order_item():

    data = request.get_json()

    order_id = data.get("order_id")
    test_catalog_id = data.get("test_catalog_id")
    contract_id = data.get("contract_id")

    price_result = get_price_for_test(
        test_catalog_id=test_catalog_id,
        contract_id=contract_id
    )

    if price_result.get("error"):
        return price_result, 404

    item = OrderItem(
        order_id=order_id,
        test_catalog_id=test_catalog_id,
        price=price_result["final_price"]
    )

    db.session.add(item)
    db.session.commit()

    return {
        "message": "Order item created successfully",
        "pricing": price_result,
        "item": item.to_dict()
    }, 201
