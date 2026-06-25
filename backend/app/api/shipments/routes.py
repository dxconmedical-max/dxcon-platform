from flask import Blueprint, request
from datetime import datetime

from app.extensions.db import db
from app.models.shipment import Shipment
from app.core.audit import write_audit


shipments_bp = Blueprint(
    "shipments",
    __name__,
    url_prefix="/api/v1/shipments"
)


def next_shipment_code():
    count = Shipment.query.count() + 1
    return f"DXCON-SHIP-{datetime.utcnow().strftime('%Y%m%d')}-{count:04d}"


@shipments_bp.route("", methods=["GET"])
@shipments_bp.route("/", methods=["GET"])
def list_shipments():
    items = Shipment.query.order_by(
        Shipment.created_at.desc()
    ).all()

    return {
        "count": len(items),
        "shipments": [x.to_dict() for x in items]
    }


@shipments_bp.route("", methods=["POST"])
@shipments_bp.route("/", methods=["POST"])
def create_shipment():
    data = request.json or {}

    item = Shipment(
        shipment_code=data.get("shipment_code") or next_shipment_code(),
        collector_id=data.get("collector_id"),
        transport_box_id=data.get("transport_box_id"),
        lab_name=data.get("lab_name"),
        sample_count=data.get("sample_count") or 0,
        temperature=data.get("temperature"),
        gps_location=data.get("gps_location"),
        status="CREATED"
    )

    db.session.add(item)
    db.session.commit()

    write_audit(
        action="CREATE_SHIPMENT",
        object_type="SHIPMENT",
        object_id=item.id,
        user_email=data.get("created_by") or "SYSTEM"
    )
    db.session.commit()

    return {
        "success": True,
        "shipment": item.to_dict()
    }, 201


@shipments_bp.route("/<shipment_id>")
def get_shipment(shipment_id):
    item = Shipment.query.get(shipment_id)

    if not item:
        item = Shipment.query.filter_by(
            shipment_code=shipment_id
        ).first()

    if not item:
        return {"error": "shipment not found"}, 404

    return item.to_dict()


@shipments_bp.route("/<shipment_id>/start", methods=["POST", "GET"])
def start_shipment(shipment_id):
    item = Shipment.query.get(shipment_id) or Shipment.query.filter_by(
        shipment_code=shipment_id
    ).first()

    if not item:
        return {"error": "shipment not found"}, 404

    item.status = "IN_TRANSIT"
    item.departed_at = datetime.utcnow()

    write_audit(
        action="SHIPMENT_IN_TRANSIT",
        object_type="SHIPMENT",
        object_id=item.id,
        user_email="COLLECTOR"
    )

    db.session.commit()

    return {
        "success": True,
        "shipment": item.to_dict()
    }


@shipments_bp.route("/<shipment_id>/arrived", methods=["POST", "GET"])
def arrived_shipment(shipment_id):
    item = Shipment.query.get(shipment_id) or Shipment.query.filter_by(
        shipment_code=shipment_id
    ).first()

    if not item:
        return {"error": "shipment not found"}, 404

    item.status = "ARRIVED"
    item.arrived_at = datetime.utcnow()

    write_audit(
        action="SHIPMENT_ARRIVED",
        object_type="SHIPMENT",
        object_id=item.id,
        user_email="COLLECTOR"
    )

    db.session.commit()

    return {
        "success": True,
        "shipment": item.to_dict()
    }


@shipments_bp.route("/<shipment_id>/receive", methods=["POST", "GET"])
def receive_shipment(shipment_id):
    data = request.json or {}

    item = Shipment.query.get(shipment_id) or Shipment.query.filter_by(
        shipment_code=shipment_id
    ).first()

    if not item:
        return {"error": "shipment not found"}, 404

    item.status = "RECEIVED"
    item.received_at = datetime.utcnow()
    item.received_by = data.get("received_by") or "LAB"
    item.receiver_note = data.get("receiver_note")

    write_audit(
        action="LAB_RECEIVED_SHIPMENT",
        object_type="SHIPMENT",
        object_id=item.id,
        user_email=item.received_by
    )

    db.session.commit()

    return {
        "success": True,
        "message": "Shipment received by lab",
        "shipment": item.to_dict()
    }


@shipments_bp.route("/scan/<qr_payload>")
def scan_qr(qr_payload):
    code = qr_payload.replace("DXCON:SHIPMENT:", "")

    item = Shipment.query.filter_by(
        shipment_code=code
    ).first()

    if not item:
        return {"error": "shipment not found"}, 404

    return {
        "success": True,
        "shipment": item.to_dict()
    }
