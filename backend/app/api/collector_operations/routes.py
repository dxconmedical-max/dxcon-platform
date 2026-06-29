from flask import Blueprint, request

from app.services.collector_operations import (
    CollectorOperationsError,
    CollectorOperationsService,
)


collector_operations_bp = Blueprint(
    "collector_operations",
    __name__,
    url_prefix="/api/v1/collector-operations",
)


def _client_ip():
    return request.remote_addr or ""


def _actor_email():
    return request.headers.get("X-User-Email", "SYSTEM")


@collector_operations_bp.route("/collectors", methods=["GET"])
def list_collectors():
    collectors = CollectorOperationsService.list_collectors(
        status=request.args.get("status")
    )
    return {
        "count": len(collectors),
        "collectors": [collector.to_dict() for collector in collectors],
    }


@collector_operations_bp.route("/collectors/<collector_id>/profile", methods=["GET"])
def get_collector_profile(collector_id):
    try:
        profile = CollectorOperationsService.get_profile(collector_id)
    except CollectorOperationsError as exc:
        return {"error": exc.message}, exc.status_code
    return profile


@collector_operations_bp.route("/collectors/<collector_id>/profile", methods=["PUT", "PATCH"])
def update_collector_profile(collector_id):
    data = request.get_json(silent=True) or {}
    try:
        collector = CollectorOperationsService.update_profile(collector_id, data)
    except CollectorOperationsError as exc:
        return {"error": exc.message}, exc.status_code
    return {"message": "Profile updated", "collector": collector.to_dict()}


@collector_operations_bp.route("/collectors/<collector_id>/vehicles", methods=["GET"])
def list_collector_vehicles(collector_id):
    vehicles = CollectorOperationsService.list_vehicles(collector_id)
    return {
        "count": len(vehicles),
        "vehicles": [vehicle.to_dict() for vehicle in vehicles],
    }


@collector_operations_bp.route("/collectors/<collector_id>/vehicles", methods=["POST"])
def create_collector_vehicle(collector_id):
    data = request.get_json(silent=True) or {}
    try:
        vehicle = CollectorOperationsService.create_vehicle(collector_id, data)
    except CollectorOperationsError as exc:
        return {"error": exc.message}, exc.status_code
    return {"message": "Vehicle created", "vehicle": vehicle.to_dict()}, 201


@collector_operations_bp.route("/collectors/<collector_id>/vehicles/<vehicle_id>/assign", methods=["POST"])
def assign_collector_vehicle(collector_id, vehicle_id):
    try:
        collector, vehicle = CollectorOperationsService.assign_active_vehicle(
            collector_id,
            vehicle_id,
        )
    except CollectorOperationsError as exc:
        return {"error": exc.message}, exc.status_code
    return {
        "message": "Active vehicle assigned",
        "collector": collector.to_dict(),
        "vehicle": vehicle.to_dict(),
    }


@collector_operations_bp.route("/collectors/<collector_id>/jobs", methods=["GET"])
def list_collector_jobs(collector_id):
    try:
        jobs = CollectorOperationsService.list_jobs(
            collector_id,
            status=request.args.get("status"),
        )
    except CollectorOperationsError as exc:
        return {"error": exc.message}, exc.status_code
    return {"count": len(jobs), "jobs": jobs}


@collector_operations_bp.route("/assignments/<assignment_id>/accept", methods=["POST"])
def accept_assignment(assignment_id):
    data = request.get_json(silent=True) or {}
    collector_id = data.get("collector_id")
    if not collector_id:
        return {"error": "collector_id is required"}, 400
    try:
        assignment = CollectorOperationsService.accept_assignment(
            assignment_id,
            collector_id,
            actor_email=_actor_email(),
            ip_address=_client_ip(),
        )
    except CollectorOperationsError as exc:
        return {"error": exc.message}, exc.status_code
    return {"message": "Assignment accepted", "assignment": assignment.to_dict()}


@collector_operations_bp.route("/collectors/<collector_id>/routes", methods=["GET"])
def list_collector_routes(collector_id):
    routes = CollectorOperationsService.list_routes(
        collector_id=collector_id,
        status=request.args.get("status"),
    )
    return {"count": len(routes), "routes": [route.to_dict() for route in routes]}


@collector_operations_bp.route("/collectors/<collector_id>/routes", methods=["POST"])
def create_collector_route(collector_id):
    data = request.get_json(silent=True) or {}
    try:
        route = CollectorOperationsService.create_route(
            collector_id,
            assignment_ids=data.get("assignment_ids"),
            transport_box_id=data.get("transport_box_id"),
        )
    except CollectorOperationsError as exc:
        return {"error": exc.message}, exc.status_code
    return {"message": "Route created", "route": route.to_dict()}, 201


@collector_operations_bp.route("/routes/<route_id>", methods=["GET"])
def get_route(route_id):
    try:
        route = CollectorOperationsService.get_route_detail(route_id)
    except CollectorOperationsError as exc:
        return {"error": exc.message}, exc.status_code
    return route


@collector_operations_bp.route("/routes/<route_id>/optimize", methods=["POST"])
def optimize_route(route_id):
    try:
        route, stops = CollectorOperationsService.optimize_route(route_id)
    except CollectorOperationsError as exc:
        return {"error": exc.message}, exc.status_code
    return {
        "message": "Route optimized",
        "route": route.to_dict(),
        "stops": [stop.to_dict() for stop in stops],
    }


@collector_operations_bp.route("/routes/<route_id>/start", methods=["POST"])
def start_route(route_id):
    data = request.get_json(silent=True) or {}
    try:
        route = CollectorOperationsService.start_route(
            route_id,
            latitude=data.get("latitude"),
            longitude=data.get("longitude"),
            actor_email=_actor_email(),
        )
    except CollectorOperationsError as exc:
        return {"error": exc.message}, exc.status_code
    return {"message": "Route started", "route": route.to_dict()}


@collector_operations_bp.route("/routes/<route_id>/complete", methods=["POST"])
def complete_route(route_id):
    try:
        route = CollectorOperationsService.complete_route(route_id, actor_email=_actor_email())
    except CollectorOperationsError as exc:
        return {"error": exc.message}, exc.status_code
    return {"message": "Route completed", "route": route.to_dict()}


@collector_operations_bp.route("/collectors/<collector_id>/check-in", methods=["POST"])
def collector_check_in(collector_id):
    data = request.get_json(silent=True) or {}
    try:
        event = CollectorOperationsService.record_check_event(
            collector_id,
            "CHECK_IN",
            booking_id=data.get("booking_id"),
            route_id=data.get("route_id"),
            latitude=data.get("latitude"),
            longitude=data.get("longitude"),
            note=data.get("note"),
            actor_email=_actor_email(),
        )
    except CollectorOperationsError as exc:
        return {"error": exc.message}, exc.status_code
    return {"message": "Check-in recorded", "event": event.to_dict()}


@collector_operations_bp.route("/collectors/<collector_id>/check-out", methods=["POST"])
def collector_check_out(collector_id):
    data = request.get_json(silent=True) or {}
    try:
        event = CollectorOperationsService.record_check_event(
            collector_id,
            "CHECK_OUT",
            booking_id=data.get("booking_id"),
            route_id=data.get("route_id"),
            latitude=data.get("latitude"),
            longitude=data.get("longitude"),
            note=data.get("note"),
            actor_email=_actor_email(),
        )
    except CollectorOperationsError as exc:
        return {"error": exc.message}, exc.status_code
    return {"message": "Check-out recorded", "event": event.to_dict()}


@collector_operations_bp.route("/bookings/<booking_id>/pickup", methods=["POST"])
def pickup_booking_sample(booking_id):
    data = request.get_json(silent=True) or {}
    collector_id = data.get("collector_id")
    if not collector_id:
        return {"error": "collector_id is required"}, 400
    try:
        collection, sample = CollectorOperationsService.pickup_sample(
            booking_id,
            collector_id,
            latitude=data.get("latitude"),
            longitude=data.get("longitude"),
            note=data.get("note"),
            actor_email=_actor_email(),
            ip_address=_client_ip(),
        )
    except CollectorOperationsError as exc:
        return {"error": exc.message}, exc.status_code
    return {
        "message": "Sample picked up",
        "collection": collection.to_dict(),
        "sample_tracking": sample.to_dict(),
    }


@collector_operations_bp.route("/collectors/<collector_id>/gps", methods=["POST"])
def record_gps(collector_id):
    data = request.get_json(silent=True) or {}
    try:
        ping = CollectorOperationsService.record_gps_ping(
            collector_id,
            latitude=data.get("latitude"),
            longitude=data.get("longitude"),
            route_id=data.get("route_id"),
            speed_kmh=data.get("speed_kmh"),
            heading=data.get("heading"),
            accuracy_m=data.get("accuracy_m"),
            actor_email=_actor_email(),
        )
    except CollectorOperationsError as exc:
        return {"error": exc.message}, exc.status_code
    return {"message": "GPS recorded", "ping": ping.to_dict()}


@collector_operations_bp.route("/collectors/<collector_id>/gps", methods=["GET"])
def get_gps_trail(collector_id):
    pings = CollectorOperationsService.get_gps_trail(
        collector_id,
        route_id=request.args.get("route_id"),
        limit=int(request.args.get("limit", 50)),
    )
    return {"count": len(pings), "pings": [ping.to_dict() for ping in pings]}


@collector_operations_bp.route("/qr/scan", methods=["POST"])
def scan_qr():
    data = request.get_json(silent=True) or {}
    qr_payload = data.get("qr_payload")
    if not qr_payload:
        return {"error": "qr_payload is required"}, 400
    try:
        result = CollectorOperationsService.scan_qr(
            qr_payload,
            collector_id=data.get("collector_id"),
            actor_email=_actor_email(),
        )
    except CollectorOperationsError as exc:
        return {"error": exc.message}, exc.status_code
    return result


@collector_operations_bp.route("/handovers", methods=["POST"])
def create_handover():
    data = request.get_json(silent=True) or {}
    collector_id = data.get("collector_id")
    handover_type = data.get("handover_type")
    object_code = data.get("object_code")
    if not collector_id or not handover_type or not object_code:
        return {"error": "collector_id, handover_type, and object_code are required"}, 400
    try:
        handover = CollectorOperationsService.create_handover(
            collector_id,
            handover_type,
            object_code,
            qr_payload=data.get("qr_payload"),
            booking_id=data.get("booking_id"),
            recipient_name=data.get("recipient_name"),
            latitude=data.get("latitude"),
            longitude=data.get("longitude"),
            note=data.get("note"),
            actor_email=_actor_email(),
        )
    except CollectorOperationsError as exc:
        return {"error": exc.message}, exc.status_code
    return {"message": "Handover recorded", "handover": handover.to_dict()}, 201


@collector_operations_bp.route("/cold-boxes/<box_id>/telemetry", methods=["POST"])
def update_cold_box(box_id):
    data = request.get_json(silent=True) or {}
    collector_id = data.get("collector_id")
    if not collector_id:
        return {"error": "collector_id is required"}, 400
    try:
        box = CollectorOperationsService.update_cold_box(
            box_id,
            collector_id,
            temperature=data.get("temperature"),
            battery_level=data.get("battery_level"),
            latitude=data.get("latitude"),
            longitude=data.get("longitude"),
            actor_email=_actor_email(),
        )
    except CollectorOperationsError as exc:
        return {"error": exc.message}, exc.status_code
    return {"message": "Cold box updated", "box": box.to_dict()}


@collector_operations_bp.route("/proofs", methods=["POST"])
def add_proof():
    data = request.get_json(silent=True) or {}
    collector_id = data.get("collector_id")
    proof_type = data.get("proof_type")
    if not collector_id or not proof_type:
        return {"error": "collector_id and proof_type are required"}, 400
    try:
        proof = CollectorOperationsService.add_proof(
            collector_id,
            proof_type,
            booking_id=data.get("booking_id"),
            route_stop_id=data.get("route_stop_id"),
            file_name=data.get("file_name"),
            content_base64=data.get("content_base64"),
            signer_name=data.get("signer_name"),
            note=data.get("note"),
            actor_email=_actor_email(),
        )
    except CollectorOperationsError as exc:
        return {"error": exc.message}, exc.status_code
    return {"message": "Proof captured", "proof": proof.to_dict()}, 201


@collector_operations_bp.route("/collectors/<collector_id>/offline/events", methods=["POST"])
def queue_offline_event(collector_id):
    data = request.get_json(silent=True) or {}
    try:
        record = CollectorOperationsService.queue_offline_event(
            collector_id,
            data.get("client_event_id"),
            data.get("event_type"),
            data.get("payload"),
        )
    except CollectorOperationsError as exc:
        return {"error": exc.message}, exc.status_code
    return {"message": "Offline event queued", "event": record.to_dict()}, 201


@collector_operations_bp.route("/collectors/<collector_id>/offline/sync", methods=["POST"])
def sync_offline_events(collector_id):
    try:
        summary = CollectorOperationsService.sync_offline_events(
            collector_id,
            actor_email=_actor_email(),
        )
    except CollectorOperationsError as exc:
        return {"error": exc.message}, exc.status_code
    return {"message": "Offline sync completed", "summary": summary}


@collector_operations_bp.route("/collectors/<collector_id>/timeline", methods=["GET"])
def list_collector_timeline(collector_id):
    timeline = CollectorOperationsService.list_timeline(
        collector_id,
        limit=int(request.args.get("limit", 50)),
    )
    return {"count": len(timeline), "timeline": [item.to_dict() for item in timeline]}


@collector_operations_bp.route("/shipments/<shipment_id>/accept", methods=["POST"])
def accept_shipment_route(shipment_id):
    data = request.get_json(silent=True) or {}
    collector_id = data.get("collector_id")
    if not collector_id:
        return {"error": "collector_id is required"}, 400
    try:
        shipment = CollectorOperationsService.accept_collector_shipment(
            shipment_id,
            collector_id,
            latitude=data.get("latitude"),
            longitude=data.get("longitude"),
            actor_email=_actor_email(),
        )
    except CollectorOperationsError as exc:
        return {"error": exc.message}, exc.status_code
    return {"message": "Shipment accepted", "shipment": shipment.to_dict()}


@collector_operations_bp.route("/shipments/<shipment_id>/start-trip", methods=["POST"])
def start_shipment_trip(shipment_id):
    data = request.get_json(silent=True) or {}
    collector_id = data.get("collector_id")
    if not collector_id:
        return {"error": "collector_id is required"}, 400
    try:
        shipment = CollectorOperationsService.start_collector_shipment_trip(
            shipment_id,
            collector_id,
            latitude=data.get("latitude"),
            longitude=data.get("longitude"),
            actor_email=_actor_email(),
        )
    except CollectorOperationsError as exc:
        return {"error": exc.message}, exc.status_code
    return {"message": "Trip started", "shipment": shipment.to_dict()}


@collector_operations_bp.route("/collectors/<collector_id>/dashboard", methods=["GET"])
def collector_dashboard(collector_id):
    try:
        dashboard = CollectorOperationsService.collector_dashboard(collector_id)
    except CollectorOperationsError as exc:
        return {"error": exc.message}, exc.status_code
    return dashboard


@collector_operations_bp.route("/supervisor/dashboard", methods=["GET"])
def supervisor_dashboard():
    return CollectorOperationsService.supervisor_dashboard()
