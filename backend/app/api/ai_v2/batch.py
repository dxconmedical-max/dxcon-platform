from flask import Blueprint

from app.models.order import Order
from app.models.clinical_summary import ClinicalSummary

from app.api.ai_v2.routes import ai_order

ai_batch_bp = Blueprint(
    "ai_batch",
    __name__,
    url_prefix="/api/v1/ai-v2"
)


@ai_batch_bp.route("/generate-all")
def generate_all():

    orders = Order.query.all()

    generated = 0

    for order in orders:

        existing = ClinicalSummary.query.filter_by(
            order_id=order.id
        ).first()

        if existing:
            continue

        try:
            ai_order(order.id)
            generated += 1
        except Exception:
            pass

    return {
        "success": True,
        "generated": generated,
        "orders": len(orders)
    }
