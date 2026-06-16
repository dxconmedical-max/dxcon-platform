from flask import Blueprint

from app.models.order_item import OrderItem
from app.models.test_result import TestResult
from app.services.ai_risk_engine import analyze_profile


ai_v2_bp = Blueprint(
    "ai_v2",
    __name__,
    url_prefix="/api/v2/ai"
)


@ai_v2_bp.route("/order/<order_id>")
def analyze_order(order_id):

    items = OrderItem.query.filter_by(
        order_id=order_id
    ).all()

    results = []

    for item in items:

        result = TestResult.query.filter_by(
            order_item_id=item.id
        ).first()

        if result:
            results.append(result)

    return analyze_profile(results)
