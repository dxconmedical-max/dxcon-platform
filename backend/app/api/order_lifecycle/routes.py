from flask import Blueprint, request

from app.services.order_lifecycle import OrderLifecycleError, OrderLifecycleService
from app.services.sample_collection_workflow import (
    SampleCollectionWorkflowError,
    SampleCollectionWorkflowService,
)


order_lifecycle_bp = Blueprint(
    "order_lifecycle",
    __name__,
    url_prefix="/api/v1/order-lifecycle",
)


def _client_ip():
    return request.remote_addr or ""


def _actor_email():
    return request.headers.get("X-User-Email", "SYSTEM")


@order_lifecycle_bp.route("/orders", methods=["GET"])
def list_orders():
    orders = OrderLifecycleService.list_orders(
        status=request.args.get("status"),
        partner_id=request.args.get("partner_id"),
    )

    return {
        "count": len(orders),
        "orders": [order.to_dict() for order in orders],
    }


@order_lifecycle_bp.route("/orders/<order_id>", methods=["GET"])
def get_order(order_id):
    try:
        payload = OrderLifecycleService.get_order_detail(order_id)
    except OrderLifecycleError as exc:
        return {"error": exc.message}, exc.status_code

    return payload


@order_lifecycle_bp.route("/bookings/<booking_id>/order", methods=["GET"])
def get_booking_order(booking_id):
    try:
        order = OrderLifecycleService.get_order_for_booking(booking_id)
    except OrderLifecycleError as exc:
        return {"error": exc.message}, exc.status_code

    if not order:
        return {"error": "Order not found for booking"}, 404

    return {"order": order.to_dict()}


@order_lifecycle_bp.route("/bookings/<booking_id>/create-order", methods=["POST"])
def create_order_from_booking(booking_id):
    try:
        order = OrderLifecycleService.create_order_from_booking(
            booking_id,
            actor_email=_actor_email(),
            ip_address=_client_ip(),
        )
    except OrderLifecycleError as exc:
        return {"error": exc.message}, exc.status_code

    return {
        "message": "Order created successfully",
        "order": order.to_dict(),
    }, 201


@order_lifecycle_bp.route("/bookings/<booking_id>/collection", methods=["GET"])
def get_booking_collection(booking_id):
    try:
        payload = SampleCollectionWorkflowService.get_collection_for_booking(booking_id)
    except SampleCollectionWorkflowError as exc:
        return {"error": exc.message}, exc.status_code

    return {
        "collection": payload,
    }


@order_lifecycle_bp.route("/bookings/<booking_id>/check-in", methods=["POST"])
def check_in_collection(booking_id):
    try:
        collection = SampleCollectionWorkflowService.check_in_collection(
            booking_id,
            actor_email=_actor_email(),
            ip_address=_client_ip(),
        )
    except SampleCollectionWorkflowError as exc:
        return {"error": exc.message}, exc.status_code

    return {
        "message": "Collector checked in successfully",
        "collection": collection.to_dict(),
    }


@order_lifecycle_bp.route("/bookings/<booking_id>/collect", methods=["POST"])
def collect_sample(booking_id):
    data = request.get_json(silent=True) or {}

    try:
        collection, sample = SampleCollectionWorkflowService.record_collection(
            booking_id,
            collector_id=data.get("collector_id"),
            note=data.get("note"),
            latitude=data.get("latitude"),
            longitude=data.get("longitude"),
            actor_email=_actor_email(),
            ip_address=_client_ip(),
        )
    except SampleCollectionWorkflowError as exc:
        return {"error": exc.message}, exc.status_code

    return {
        "message": "Sample collected successfully",
        "collection": collection.to_dict(),
        "sample_tracking": sample.to_dict(),
    }


@order_lifecycle_bp.route("/bookings/<booking_id>/dispatch", methods=["POST"])
def dispatch_sample(booking_id):
    data = request.get_json(silent=True) or {}

    try:
        collection, sample = SampleCollectionWorkflowService.dispatch_sample(
            booking_id,
            transport_box_id=data.get("transport_box_id"),
            note=data.get("note"),
            actor_email=_actor_email(),
            ip_address=_client_ip(),
        )
    except SampleCollectionWorkflowError as exc:
        return {"error": exc.message}, exc.status_code

    return {
        "message": "Sample dispatched successfully",
        "collection": collection.to_dict(),
        "sample_tracking": sample.to_dict(),
    }


@order_lifecycle_bp.route("/bookings/<booking_id>/lab-receive", methods=["POST"])
def receive_at_lab(booking_id):
    data = request.get_json(silent=True) or {}

    try:
        collection, sample = SampleCollectionWorkflowService.receive_at_lab(
            booking_id,
            note=data.get("note"),
            actor_email=_actor_email(),
            ip_address=_client_ip(),
        )
    except SampleCollectionWorkflowError as exc:
        return {"error": exc.message}, exc.status_code

    return {
        "message": "Sample received at lab successfully",
        "collection": collection.to_dict(),
        "sample_tracking": sample.to_dict(),
    }
