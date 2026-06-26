from flask import Blueprint, request

from app.extensions.db import db
from app.models.shipment import Shipment
from app.models.shipment_item import ShipmentItem
from app.models.shipment_timeline import ShipmentTimeline
from app.models.event_log import EventLog
from app.core.events import write_event
from app.core.audit import write_audit
from app.core.qr_service import parse_qr_payload


logistics_v2_bp = Blueprint(
    "logistics_v2",
    __name__,
    url_prefix="/api/v1/logistics-v2"
)


@logistics_v2_bp.route("/shipments/<shipment_id>/items")
def shipment_items(shipment_id):
    items = ShipmentItem.query.filter_by(
        shipment_id=shipment_id
    ).all()

    return {
        "count": len(items),
        "items": [x.to_dict() for x in items]
    }


@logistics_v2_bp.route("/shipments/<shipment_id>/items", methods=["POST"])
def add_shipment_item(shipment_id):
    data = request.json or {}

    item = ShipmentItem(
        shipment_id=shipment_id,
        order_id=data.get("order_id"),
        order_item_id=data.get("order_item_id"),
        sample_tracking_id=data.get("sample_tracking_id"),
        sample_code=data.get("sample_code"),
        tube_type=data.get("tube_type"),
        test_name=data.get("test_name"),
        status=data.get("status") or "CREATED"
    )

    db.session.add(item)

    write_event(
        event_type="SHIPMENT_ITEM_ADDED",
        object_type="SHIPMENT",
        object_id=shipment_id,
        message=f"Sample added: {item.sample_code}"
    )

    db.session.commit()

    return {
        "success": True,
        "item": item.to_dict()
    }, 201


@logistics_v2_bp.route("/shipments/<shipment_id>/timeline")
def shipment_timeline(shipment_id):
    items = ShipmentTimeline.query.filter_by(
        shipment_id=shipment_id
    ).order_by(
        ShipmentTimeline.created_at.asc()
    ).all()

    return {
        "count": len(items),
        "timeline": [x.to_dict() for x in items]
    }


@logistics_v2_bp.route("/shipments/<shipment_id>/timeline", methods=["POST"])
def add_timeline_event(shipment_id):
    data = request.json or {}

    item = ShipmentTimeline(
        shipment_id=shipment_id,
        event_type=data.get("event_type") or "EVENT",
        note=data.get("note"),
        actor=data.get("actor"),
        gps_location=data.get("gps_location"),
        temperature=data.get("temperature")
    )

    db.session.add(item)

    write_event(
        event_type=item.event_type,
        object_type="SHIPMENT",
        object_id=shipment_id,
        message=item.note
    )

    db.session.commit()

    return {
        "success": True,
        "timeline": item.to_dict()
    }, 201


@logistics_v2_bp.route("/scan", methods=["POST"])
def scan_qr():
    data = request.json or {}
    payload = data.get("payload") or ""

    parsed = parse_qr_payload(payload)

    if not parsed["valid"]:
        return {
            "success": False,
            "error": "invalid QR payload"
        }, 400

    object_type = parsed["type"]
    code = parsed["code"]

    if object_type == "SHIPMENT":
        shipment = Shipment.query.filter_by(
            shipment_code=code
        ).first()

        if not shipment:
            return {"success": False, "error": "shipment not found"}, 404

        return {
            "success": True,
            "type": "SHIPMENT",
            "shipment": shipment.to_dict()
        }

    if object_type == "SAMPLE":
        item = ShipmentItem.query.filter_by(
            sample_code=code
        ).first()

        if not item:
            return {"success": False, "error": "sample not found"}, 404

        return {
            "success": True,
            "type": "SAMPLE",
            "item": item.to_dict()
        }

    return {
        "success": False,
        "error": "unsupported QR type"
    }, 400


@logistics_v2_bp.route("/events")
def events():
    items = EventLog.query.order_by(
        EventLog.created_at.desc()
    ).limit(200).all()

    return {
        "count": len(items),
        "events": [x.to_dict() for x in items]
    }
