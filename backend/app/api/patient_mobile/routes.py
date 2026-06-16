from flask import Blueprint

from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.test_result import TestResult
from app.models.home_collection import HomeCollection
from app.models.sample_tracking import SampleTracking


patient_mobile_bp = Blueprint(
    "patient_mobile",
    __name__,
    url_prefix="/api/v1/patient"
)


@patient_mobile_bp.route("/orders/<patient_id>")
def patient_orders(patient_id):

    orders = Order.query.filter_by(
        patient_id=patient_id
    ).all()

    return {
        "count": len(orders),
        "orders": [
            order.to_dict()
            for order in orders
        ]
    }


@patient_mobile_bp.route("/results/<patient_id>")
def patient_results(patient_id):

    orders = Order.query.filter_by(
        patient_id=patient_id
    ).all()

    results = []

    for order in orders:

        items = OrderItem.query.filter_by(
            order_id=order.id
        ).all()

        for item in items:

            test_result = TestResult.query.filter_by(
                order_item_id=item.id
            ).first()

            if test_result:
                results.append(
                    test_result.to_dict()
                )

    return {
        "count": len(results),
        "results": results
    }


@patient_mobile_bp.route("/report/<order_id>")
def patient_report(order_id):

    return {
        "pdf_url":
        f"/results/report/{order_id}/pdf"
    }


@patient_mobile_bp.route("/home-collections/<patient_id>")
def patient_home_collections(patient_id):

    collections = HomeCollection.query.filter_by(
        patient_id=patient_id
    ).all()

    return {
        "count": len(collections),
        "home_collections": [
            item.to_dict()
            for item in collections
        ]
    }


@patient_mobile_bp.route("/tracking/<patient_id>")
def patient_tracking(patient_id):

    orders = Order.query.filter_by(
        patient_id=patient_id
    ).all()

    tracking = []

    for order in orders:

        samples = SampleTracking.query.all()

        for sample in samples:

            tracking.append(
                sample.to_dict()
            )

    return {
        "count": len(tracking),
        "tracking": tracking
    }
