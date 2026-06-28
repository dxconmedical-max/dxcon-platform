from flask import Blueprint, request

from app.services.incident_service import IncidentService, IncidentServiceError
from app.services.order_workflow_service import OrderWorkflowError, OrderWorkflowService
from app.services.sample_tracking_service import SampleTrackingService, SampleTrackingServiceError


order_execution_bp = Blueprint(
    "order_execution",
    __name__,
    url_prefix="/api/v1/order-execution",
)


def _client_ip():
    return request.remote_addr or ""


def _actor_email():
    return request.headers.get("X-User-Email", "SYSTEM")


@order_execution_bp.route("/orders", methods=["GET"])
def list_orders():
    orders = OrderWorkflowService.list_orders(
        status=request.args.get("status"),
        partner_id=request.args.get("partner_id"),
    )
    return {
        "count": len(orders),
        "orders": [order.to_dict() for order in orders],
    }


@order_execution_bp.route("/orders", methods=["POST"])
def create_order():
    data = request.get_json(silent=True) or {}
    booking_id = data.get("booking_id")
    if not booking_id:
        return {"error": "booking_id is required"}, 400
    try:
        order = OrderWorkflowService.create_from_booking(
            booking_id,
            actor_email=_actor_email(),
            ip_address=_client_ip(),
        )
    except OrderWorkflowError as exc:
        return {"error": exc.message}, exc.status_code
    return {"message": "Medical order created", "order": order.to_dict()}, 201


@order_execution_bp.route("/orders/<order_id>", methods=["GET"])
def get_order(order_id):
    try:
        payload = OrderWorkflowService.get_order_detail(order_id)
    except OrderWorkflowError as exc:
        return {"error": exc.message}, exc.status_code
    return payload


@order_execution_bp.route("/orders/<order_id>/timeline", methods=["GET"])
def get_order_timeline(order_id):
    try:
        timeline = OrderWorkflowService.list_timeline(order_id)
    except OrderWorkflowError as exc:
        return {"error": exc.message}, exc.status_code
    return {
        "count": len(timeline),
        "timeline": [event.to_dict() for event in timeline],
    }


@order_execution_bp.route("/orders/<order_id>/barcode", methods=["GET"])
def get_order_barcode(order_id):
    try:
        payload = OrderWorkflowService.get_barcode(order_id)
    except OrderWorkflowError as exc:
        return {"error": exc.message}, exc.status_code
    return payload


@order_execution_bp.route("/orders/<order_id>/label", methods=["GET", "POST"])
def order_label(order_id):
    data = request.get_json(silent=True) or {}
    try:
        label, payload = SampleTrackingService.create_label(
            order_id,
            template_name=data.get("template_name", "STANDARD"),
            mark_printed=request.method == "POST" or data.get("mark_printed"),
        )
    except (OrderWorkflowError, SampleTrackingServiceError) as exc:
        return {"error": exc.message}, exc.status_code

    if request.method == "POST":
        return {
            "message": "Label generated and marked printed",
            "label": label.to_dict(),
            "print_payload": payload,
        }, 201

    return {
        "label": label.to_dict(),
        "print_payload": payload,
    }


@order_execution_bp.route("/orders/<order_id>/incident", methods=["GET", "POST"])
def order_incident(order_id):
    if request.method == "GET":
        try:
            incidents = IncidentService.list_incidents(order_id)
        except IncidentServiceError as exc:
            return {"error": exc.message}, exc.status_code
        return {
            "count": len(incidents),
            "incidents": [incident.to_dict() for incident in incidents],
        }

    data = request.get_json(silent=True) or {}
    try:
        incident = IncidentService.log_incident(
            order_id,
            incident_type=data.get("incident_type"),
            description=data.get("description"),
            sample_id=data.get("sample_id"),
            severity=data.get("severity", "MEDIUM"),
            reported_by=data.get("reported_by", _actor_email()),
            actor_email=_actor_email(),
            ip_address=_client_ip(),
        )
    except IncidentServiceError as exc:
        return {"error": exc.message}, exc.status_code
    return {"message": "Incident logged", "incident": incident.to_dict()}, 201


@order_execution_bp.route("/orders/<order_id>/cancel", methods=["POST"])
def cancel_order(order_id):
    data = request.get_json(silent=True) or {}
    try:
        order = OrderWorkflowService.cancel_order(
            order_id,
            reason=data.get("reason"),
            actor_email=_actor_email(),
            ip_address=_client_ip(),
        )
    except OrderWorkflowError as exc:
        return {"error": exc.message}, exc.status_code
    return {"message": "Order cancelled", "order": order.to_dict()}


@order_execution_bp.route("/orders/<order_id>/refund", methods=["POST"])
def refund_order(order_id):
    data = request.get_json(silent=True) or {}
    try:
        order = OrderWorkflowService.refund_order(
            order_id,
            reason=data.get("reason"),
            actor_email=_actor_email(),
            ip_address=_client_ip(),
        )
    except OrderWorkflowError as exc:
        return {"error": exc.message}, exc.status_code
    return {"message": "Order refunded", "order": order.to_dict()}


@order_execution_bp.route("/orders/<order_id>/recollect", methods=["POST"])
def recollect_order(order_id):
    data = request.get_json(silent=True) or {}
    try:
        order, recollect = OrderWorkflowService.request_recollect(
            order_id,
            reason=data.get("reason"),
            scheduled_date=data.get("scheduled_date"),
            actor_email=_actor_email(),
            ip_address=_client_ip(),
        )
    except OrderWorkflowError as exc:
        return {"error": exc.message}, exc.status_code
    return {
        "message": "Recollect requested",
        "order": order.to_dict(),
        "recollect_request": recollect.to_dict(),
    }


@order_execution_bp.route("/orders/<order_id>/transition", methods=["POST"])
def transition_order(order_id):
    data = request.get_json(silent=True) or {}
    target_status = data.get("status")
    if not target_status:
        return {"error": "status is required"}, 400
    try:
        order = OrderWorkflowService.transition(
            order_id,
            target_status,
            message=data.get("message"),
            actor_email=_actor_email(),
            ip_address=_client_ip(),
            collector_id=data.get("collector_id"),
        )
    except OrderWorkflowError as exc:
        return {"error": exc.message}, exc.status_code
    return {"message": "Order transitioned", "order": order.to_dict()}


@order_execution_bp.route("/orders/<order_id>/advance", methods=["POST"])
def advance_order(order_id):
    try:
        order, steps = OrderWorkflowService.advance_booking_workflow(
            order_id,
            actor_email=_actor_email(),
            ip_address=_client_ip(),
        )
    except OrderWorkflowError as exc:
        return {"error": exc.message}, exc.status_code
    return {"message": "Order advanced", "order": order.to_dict(), "steps": steps}
