from pathlib import Path

p = Path("app/api/shipments/routes.py")
text = p.read_text()

if "from app.models.transport_box import TransportBox" not in text:
    text = text.replace(
        "from app.models.shipment import Shipment\n",
        "from app.models.shipment import Shipment\nfrom app.models.transport_box import TransportBox\n"
    )

append = r'''


@shipments_bp.route("/<shipment_id>/assign-box/<box_id>", methods=["POST", "GET"])
def assign_box_to_shipment(shipment_id, box_id):
    item = Shipment.query.get(shipment_id) or Shipment.query.filter_by(
        shipment_code=shipment_id
    ).first()

    if not item:
        return {"success": False, "error": "shipment not found"}, 404

    box = TransportBox.query.get(box_id) or TransportBox.query.filter_by(
        box_code=box_id
    ).first()

    if not box:
        return {"success": False, "error": "box not found"}, 404

    item.transport_box_id = box.id
    box.status = "IN_USE"

    if hasattr(box, "current_shipment_id"):
        box.current_shipment_id = item.id

    write_audit(
        action="ASSIGN_BOX_TO_SHIPMENT",
        object_type="SHIPMENT",
        object_id=item.id,
        user_email="LOGISTICS"
    )

    db.session.commit()

    return {
        "success": True,
        "message": "Box assigned to shipment",
        "shipment": item.to_dict(),
        "box": box.to_dict() if hasattr(box, "to_dict") else {
            "id": box.id,
            "box_code": box.box_code,
            "status": box.status
        }
    }


@shipments_bp.route("/receive-by-box/<box_id>", methods=["POST", "GET"])
def receive_shipment_by_box(box_id):
    data = request.json or {}

    box = TransportBox.query.get(box_id) or TransportBox.query.filter_by(
        box_code=box_id
    ).first()

    if not box:
        return {"success": False, "error": "box not found"}, 404

    shipment = None

    if hasattr(box, "current_shipment_id") and box.current_shipment_id:
        shipment = Shipment.query.get(box.current_shipment_id)

    if not shipment:
        shipment = Shipment.query.filter_by(
            transport_box_id=box.id
        ).order_by(
            Shipment.created_at.desc()
        ).first()

    if not shipment:
        return {
            "success": False,
            "error": "no active shipment found for box"
        }, 404

    shipment.status = "RECEIVED"
    shipment.received_at = datetime.utcnow()
    shipment.received_by = data.get("received_by") or "LAB"
    shipment.receiver_note = data.get("receiver_note") or "Received by box QR"

    box.status = "RETURNING"

    write_audit(
        action="LAB_RECEIVED_SHIPMENT_BY_BOX",
        object_type="SHIPMENT",
        object_id=shipment.id,
        user_email=shipment.received_by
    )

    db.session.commit()

    return {
        "success": True,
        "message": "Shipment received by lab via box QR",
        "shipment": shipment.to_dict(),
        "box": box.to_dict() if hasattr(box, "to_dict") else {
            "id": box.id,
            "box_code": box.box_code,
            "status": box.status
        }
    }
'''

if "assign_box_to_shipment" not in text:
    text += append

p.write_text(text)
print("shipment box binding endpoints installed")
