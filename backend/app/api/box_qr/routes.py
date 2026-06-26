from flask import Blueprint
from app.models.transport_box import TransportBox
from app.core.qr_service import box_qr_payload

box_qr_bp = Blueprint(
    "box_qr",
    __name__,
    url_prefix="/api/v1/box-qr"
)


@box_qr_bp.route("/<box_id>")
def get_box_qr(box_id):
    box = TransportBox.query.get(box_id)

    if not box:
        box = TransportBox.query.filter_by(
            box_code=box_id
        ).first()

    if not box:
        return {"success": False, "error": "box not found"}, 404

    return {
        "success": True,
        "box_id": box.id,
        "box_code": box.box_code,
        "qr_payload": box_qr_payload(box.box_code)
    }
