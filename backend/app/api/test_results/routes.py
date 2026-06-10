
from flask import Blueprint, request

from app.extensions.db import db
from app.models.test_result import TestResult
from app.models.order_item import OrderItem
from app.services.result_flag import calculate_result_flag
from app.services.order_status import update_order_status


test_results_bp = Blueprint(
    "test_results",
    __name__,
    url_prefix="/api/v1/test-results"
)


@test_results_bp.route("", methods=["GET"])
def get_results():

    results = TestResult.query.all()

    return {
        "count": len(results),
        "results": [
            result.to_dict()
            for result in results
        ]
    }


@test_results_bp.route("", methods=["POST"])
def create_result():

    data = request.get_json()

    flag = calculate_result_flag(
        data.get("result_value"),
        data.get("reference_range")
    )

    result = TestResult(
        order_item_id=data.get("order_item_id"),
        test_name=data.get("test_name"),
        result_value=data.get("result_value"),
        unit=data.get("unit"),
        reference_range=data.get("reference_range"),
        flag=flag,
        interpretation=data.get("interpretation")
    )

    db.session.add(result)
    db.session.commit()

    order_item = OrderItem.query.get(
        result.order_item_id
    )

    if order_item:
        update_order_status(
            order_item.order_id
        )

    return {
        "message": "Result created",
        "result": result.to_dict()
    }, 201
