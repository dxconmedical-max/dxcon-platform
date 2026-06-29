from flask import Blueprint, request

from app.services.logistics_platform_service import (
    DispatchBoardService,
    DriverService,
    ETAService,
    LogisticsError,
    ProofOfDeliveryService,
    RouteOptimizationService,
    VehicleService,
)


logistics_platform_bp = Blueprint(
    "logistics_platform",
    __name__,
    url_prefix="/api/v1/logistics",
)


def _page_args():
    return request.args.get("page", 1), request.args.get("per_page", 20)


def _error(exc):
    return {"error": exc.message}, exc.status_code


def _actor():
    return request.headers.get("X-User-Email", "SYSTEM")


@logistics_platform_bp.route("/drivers", methods=["GET"])
def list_drivers():
    page, per_page = _page_args()
    return DriverService.list_drivers(
        page=page,
        per_page=per_page,
        status=request.args.get("status"),
        hub_city=request.args.get("hub_city"),
        q=request.args.get("q"),
    )


@logistics_platform_bp.route("/drivers", methods=["POST"])
def create_driver():
    data = request.get_json(silent=True) or {}
    if not data.get("full_name"):
        return {"error": "full_name is required"}, 400
    profile = DriverService.create_driver(data)
    return {"message": "Driver profile created", "driver": profile.to_dict()}, 201


@logistics_platform_bp.route("/vehicles", methods=["GET"])
def list_vehicles():
    page, per_page = _page_args()
    return VehicleService.list_vehicles(
        page=page,
        per_page=per_page,
        status=request.args.get("status"),
        vehicle_type=request.args.get("vehicle_type"),
        q=request.args.get("q"),
    )


@logistics_platform_bp.route("/vehicles", methods=["POST"])
def create_vehicle():
    data = request.get_json(silent=True) or {}
    if not data.get("plate_number"):
        return {"error": "plate_number is required"}, 400
    vehicle = VehicleService.create_vehicle(data)
    return {"message": "Vehicle created", "vehicle": vehicle.to_dict()}, 201


@logistics_platform_bp.route("/routes", methods=["GET"])
def list_routes():
    page, per_page = _page_args()
    return RouteOptimizationService.list_routes(
        page=page,
        per_page=per_page,
        status=request.args.get("status"),
        driver_profile_id=request.args.get("driver_profile_id"),
        q=request.args.get("q"),
    )


@logistics_platform_bp.route("/routes", methods=["POST"])
def create_route():
    data = request.get_json(silent=True) or {}
    route = RouteOptimizationService.create_route(data)
    return {"message": "Route created", "route": route.to_dict()}, 201


@logistics_platform_bp.route("/routes/<route_id>", methods=["GET"])
def get_route(route_id):
    try:
        return {"route": RouteOptimizationService.get_route(route_id)}
    except LogisticsError as exc:
        return _error(exc)


@logistics_platform_bp.route("/routes/optimize", methods=["POST"])
def optimize_route():
    data = request.get_json(silent=True) or {}
    route_id = data.get("route_id")
    if not route_id:
        return {"error": "route_id is required"}, 400
    try:
        route = RouteOptimizationService.optimize_route(route_id)
    except LogisticsError as exc:
        return _error(exc)
    return {"message": "Route optimized", "route": route}


@logistics_platform_bp.route("/dispatch-board", methods=["GET"])
def dispatch_board():
    return DispatchBoardService.get_board()


@logistics_platform_bp.route("/assign", methods=["POST"])
def assign_dispatch():
    data = request.get_json(silent=True) or {}
    if not data.get("driver_profile_id"):
        return {"error": "driver_profile_id is required"}, 400
    data["actor"] = _actor()
    try:
        assignment = DispatchBoardService.assign(data)
    except LogisticsError as exc:
        return _error(exc)
    return {"message": "Dispatch assigned", "assignment": assignment.to_dict()}, 201


@logistics_platform_bp.route("/gps", methods=["POST"])
def record_gps():
    data = request.get_json(silent=True) or {}
    if data.get("latitude") is None or data.get("longitude") is None:
        return {"error": "latitude and longitude are required"}, 400
    ping = ProofOfDeliveryService.record_gps(data)
    return {"message": "GPS ping recorded", "gps_ping": ping.to_dict()}, 201


@logistics_platform_bp.route("/proof", methods=["POST"])
def record_proof():
    data = request.get_json(silent=True) or {}
    data["captured_by"] = data.get("captured_by") or _actor()
    proof = ProofOfDeliveryService.record_proof(data)
    return {"message": "Delivery proof recorded", "proof": proof.to_dict()}, 201


@logistics_platform_bp.route("/routes/<route_id>/eta", methods=["GET"])
def route_eta(route_id):
    return ETAService.list_estimates(route_id)
