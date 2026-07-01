from flask import Blueprint, request

from app.services.federation_capacity_service import CapacityService
from app.services.federation_failover_service import FailoverService
from app.services.federation_routing_service import SmartRoutingService
from app.services.federation_service import (
    FederationCapabilityService,
    FederationError,
    FederationProviderService,
    FederationService,
)


federation_bp = Blueprint(
    "federation",
    __name__,
    url_prefix="/api/v1/federation",
)


def _page_args():
    return (
        max(int(request.args.get("page", 1)), 1),
        min(max(int(request.args.get("page_size", 50)), 1), 200),
    )


def _actor():
    return request.headers.get("X-User-Email", "SYSTEM")


def _error(exc):
    return {"error": exc.message}, exc.status_code


@federation_bp.route("/labs", methods=["GET"])
def list_labs():
    page, page_size = _page_args()
    return FederationService.list_labs(
        status=request.args.get("status"),
        provider_id=request.args.get("provider_id"),
        page=page,
        page_size=page_size,
    )


@federation_bp.route("/labs", methods=["POST"])
def create_lab():
    data = request.get_json(silent=True) or {}
    try:
        lab = FederationService.create_lab(data)
    except FederationError as exc:
        return _error(exc)
    return {"message": "Federated lab created", "lab": lab.to_dict()}, 201


@federation_bp.route("/labs/<lab_id>", methods=["GET"])
def get_lab(lab_id):
    try:
        return FederationService.get_lab(lab_id)
    except FederationError as exc:
        return _error(exc)


@federation_bp.route("/labs/<lab_id>/connect", methods=["POST"])
def connect_lab(lab_id):
    try:
        lab = FederationService.connect_lab(lab_id, actor_email=_actor())
    except FederationError as exc:
        return _error(exc)
    return {"message": "Lab connected", "lab": lab.to_dict()}


@federation_bp.route("/labs/<lab_id>/disconnect", methods=["POST"])
def disconnect_lab(lab_id):
    try:
        lab = FederationService.disconnect_lab(lab_id, actor_email=_actor())
    except FederationError as exc:
        return _error(exc)
    return {"message": "Lab disconnected", "lab": lab.to_dict()}


@federation_bp.route("/providers", methods=["GET"])
def list_providers():
    page, page_size = _page_args()
    return FederationProviderService.list_providers(
        page=page,
        page_size=page_size,
        status=request.args.get("status"),
    )


@federation_bp.route("/providers", methods=["POST"])
def create_provider():
    data = request.get_json(silent=True) or {}
    try:
        provider = FederationProviderService.create_provider(data)
    except FederationError as exc:
        return _error(exc)
    return {"message": "Provider created", "provider": provider.to_dict()}, 201


@federation_bp.route("/capacity", methods=["GET"])
def get_capacity():
    return CapacityService.get_capacity(request.args.get("lab_id"))


@federation_bp.route("/capacity/update", methods=["POST"])
def update_capacity():
    data = request.get_json(silent=True) or {}
    try:
        return CapacityService.update_capacity(data)
    except FederationError as exc:
        return _error(exc)


@federation_bp.route("/capacity/history", methods=["GET"])
def capacity_history():
    page, page_size = _page_args()
    return CapacityService.history(
        lab_id=request.args.get("lab_id"),
        days=int(request.args.get("days", 7)),
        page=page,
        page_size=page_size,
    )


@federation_bp.route("/route", methods=["POST"])
def route_request():
    data = request.get_json(silent=True) or {}
    try:
        return SmartRoutingService.route(data, actor_email=_actor())
    except FederationError as exc:
        return _error(exc)


@federation_bp.route("/routing-decisions", methods=["GET"])
def routing_decisions():
    page, page_size = _page_args()
    return SmartRoutingService.list_decisions(page=page, page_size=page_size)


@federation_bp.route("/routing-audit", methods=["GET"])
def routing_audit():
    page, page_size = _page_args()
    return SmartRoutingService.list_audit(page=page, page_size=page_size)


@federation_bp.route("/failover/check", methods=["POST"])
def failover_check():
    data = request.get_json(silent=True) or {}
    try:
        return FailoverService.check(data)
    except FederationError as exc:
        return _error(exc)


@federation_bp.route("/failover/events", methods=["GET"])
def failover_events():
    page, page_size = _page_args()
    return FailoverService.list_events(
        page=page,
        page_size=page_size,
        trigger_type=request.args.get("trigger_type"),
    )
