from flask import Blueprint, request

from app.extensions.db import db
from app.models.transport_box import TransportBox


transport_boxes_bp = Blueprint(
    "transport_boxes",
    __name__,
    url_prefix="/api/v1/transport-boxes"
)


@transport_boxes_bp.route("", methods=["GET"])
def get_transport_boxes():

    boxes = TransportBox.query.all()

    return {
        "count": len(boxes),
        "data": [
            box.to_dict()
            for box in boxes
        ]
    }


@transport_boxes_bp.route("", methods=["POST"])
def create_transport_box():

    data = request.get_json()

    box = TransportBox(
        box_code=data.get("box_code"),
        temperature=float(data.get("temperature", 4.0)),
        battery_level=int(data.get("battery_level", 100)),
        latitude=data.get("latitude"),
        longitude=data.get("longitude"),
        status=data.get("status", "ONLINE")
    )

    box.update_alert_status()

    db.session.add(box)
    db.session.commit()

    return {
        "message": "Transport box created",
        "data": box.to_dict()
    }, 201


@transport_boxes_bp.route("/<box_id>", methods=["PATCH"])
def update_transport_box(box_id):

    box = TransportBox.query.get(box_id)

    if not box:
        return {
            "error": "Transport box not found"
        }, 404

    data = request.get_json()

    if "temperature" in data:
        box.temperature = float(data.get("temperature"))

    if "battery_level" in data:
        box.battery_level = int(data.get("battery_level"))

    if "latitude" in data:
        box.latitude = data.get("latitude")

    if "longitude" in data:
        box.longitude = data.get("longitude")

    if "status" in data:
        box.status = data.get("status")

    box.update_alert_status()

    db.session.commit()

    return {
        "message": "Transport box updated",
        "data": box.to_dict()
    }
