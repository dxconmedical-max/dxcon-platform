import math
from datetime import datetime, timezone

from flask import Blueprint, current_app, request

from app.core.authenticated_identity import get_authenticated_identity
from app.core.authz import roles_required
from app.core.patient_scope import is_internal_org
from app.services import live_location_store as store

live_location_bp = Blueprint(
    "live_location",
    __name__,
    url_prefix="/api/v1/live-location",
)

_SENDERS = ("COLLECTOR", "PARTNER_COLLECTOR", "DRIVER")
_VIEWERS_ANY_ORG = ("SUPER_ADMIN", "SYSTEM_ADMIN")
_VIEWERS_INTERNAL = ("ADMIN", "RECEPTION")


def _number(value, low, high):
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(number) or number < low or number > high:
        return None
    return number


def _optional(value, low, high):
    if value is None:
        return None
    return _number(value, low, high)


@live_location_bp.route("/ping", methods=["POST"])
@roles_required(*_SENDERS)
def ping():
    data = request.get_json(silent=True) or {}
    latitude = _number(data.get("latitude"), -90, 90)
    longitude = _number(data.get("longitude"), -180, 180)
    if latitude is None or longitude is None:
        return {"success": False, "error": "latitude and longitude are invalid"}, 400

    identity = get_authenticated_identity()
    payload = {
        "user_id": identity.user_id,
        "email": identity.email,
        "latitude": latitude,
        "longitude": longitude,
        "accuracy_m": _optional(data.get("accuracy_m"), 0, 100000),
        "heading": _optional(data.get("heading"), 0, 360),
        "speed_kmh": _optional(data.get("speed_kmh"), 0, 400),
        "recorded_at": datetime.now(timezone.utc).isoformat(),
    }
    store.put(current_app, identity.user_id, payload)
    return {"success": True}


@live_location_bp.route("/ping", methods=["DELETE"])
@roles_required(*_SENDERS)
def stop():
    identity = get_authenticated_identity()
    store.remove(current_app, identity.user_id)
    return {"success": True}


@live_location_bp.route("/collectors", methods=["GET"])
@roles_required(*_VIEWERS_ANY_ORG, *_VIEWERS_INTERNAL)
def collectors():
    identity = get_authenticated_identity()
    if identity.platform_role not in _VIEWERS_ANY_ORG and not is_internal_org(
        identity.organization_id
    ):
        return {"success": False, "error": "DxCon staff only"}, 403
    items = store.list_all(current_app)
    return {"success": True, "collectors": items, "ttl_seconds": store.TTL_SECONDS}
