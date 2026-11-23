from flask import Blueprint, current_app, request
from sqlalchemy import func

from app.business_engine import service as biz
from app.business_engine.service import BusinessEngineError
from app.core.audit import write_audit
from app.core.authenticated_identity import authenticated_actor_email, get_authenticated_identity
from app.core.authz import roles_required
from app.core.patient_scope import is_internal_org
from app.extensions.db import db
from app.models.biz_order import BizOrder, BizPayment
from app.services import momo

momo_payments_bp = Blueprint("momo_payments", __name__, url_prefix="/api/v1")

_ANY_ORG = ("SUPER_ADMIN", "SYSTEM_ADMIN")
_INTERNAL = ("ADMIN", "RECEPTION")


def _find_order(ref: str):
    return BizOrder.query.filter((BizOrder.order_code == ref) | (BizOrder.id == ref)).first()


def _outstanding(order) -> float:
    paid = db.session.query(func.coalesce(func.sum(BizPayment.amount), 0)).filter(BizPayment.order_id == order.id).scalar()
    return round(max(0.0, float(order.total_amount or 0) - float(paid or 0)), 2)


def _staff_gate():
    identity = get_authenticated_identity()
    if identity.platform_role not in _ANY_ORG and not is_internal_org(identity.organization_id):
        return {"success": False, "error": "DxCon staff only"}, 403
    return None


@momo_payments_bp.route("/payments/momo/create", methods=["POST"])
@roles_required(*_ANY_ORG, *_INTERNAL)
def momo_create():
    denied = _staff_gate()
    if denied:
        return denied
    body = request.get_json(silent=True) or {}
    order = _find_order(str(body.get("order_ref") or body.get("order_code") or ""))
    if order is None:
        return {"success": False, "error": "Order not found"}, 404
    outstanding = _outstanding(order)
    if outstanding <= 0:
        return {"success": False, "error": "Đơn đã thanh toán đủ."}, 409
    api = (current_app.config.get("PUBLIC_API_URL") or "https://api.dxcon.com.vn").rstrip("/")
    site = (current_app.config.get("PUBLIC_SITE_URL") or "https://dxcon.com.vn").rstrip("/")
    try:
        data = momo.create_payment(
            order_code=order.order_code,
            amount=int(round(outstanding)),
            order_info=f"DxCon {order.order_code}",
            ipn_url=f"{api}/api/v1/public/payments/momo/ipn",
            redirect_url=f"{site}/app/reception",
        )
    except momo.MoMoError as exc:
        return {"success": False, "error": exc.message}, exc.status_code
    from app.reception_workspace.qr_engine import render_qr_png_data_url

    qr_source = data.get("qr_code_url") or data.get("pay_url") or ""
    data["qr_png"] = render_qr_png_data_url(qr_source) if qr_source else None
    write_audit("MOMO_PAYMENT_REQUESTED", "BizOrder", order.order_code, user_email=authenticated_actor_email())
    db.session.commit()
    return {"success": True, "data": data}, 200


@momo_payments_bp.route("/payments/momo/check/<order_ref>", methods=["GET"])
@roles_required(*_ANY_ORG, *_INTERNAL)
def momo_check(order_ref: str):
    denied = _staff_gate()
    if denied:
        return denied
    order = _find_order(order_ref)
    if order is None:
        return {"success": False, "error": "Order not found"}, 404
    outstanding = _outstanding(order)
    return {"success": True, "data": {"paid": outstanding <= 0, "outstanding": outstanding}}, 200


@momo_payments_bp.route("/public/payments/momo/ipn", methods=["POST"])
def momo_ipn():
    payload = request.get_json(silent=True) or {}
    if not momo.verify_ipn(payload):
        return {"success": False, "error": "invalid signature"}, 400
    if int(payload.get("resultCode", -1)) != 0:
        return "", 204  # failed or cancelled payment: acknowledge, record nothing
    order_code = momo.parse_order_code(str(payload.get("orderId", "")))
    trans_id = str(payload.get("transId", ""))
    order = _find_order(order_code or "")
    if order is None or not trans_id:
        return {"success": False, "error": "unknown order"}, 400
    receipt = f"MOMO-{trans_id}"[:50]
    if BizPayment.query.filter_by(receipt_number=receipt).first():
        return "", 204  # MoMo retries IPN; already recorded
    try:
        biz.record_order_payment(
            order.order_code,
            payment_method="momo",
            amount=float(payload.get("amount") or 0),
            receipt_number=receipt,
            actor="momo-ipn",
        )
        write_audit("MOMO_PAYMENT_RECORDED", "BizOrder", order.order_code, user_email="momo-ipn")
        db.session.commit()
    except BusinessEngineError as exc:
        db.session.rollback()
        current_app.logger.warning("momo ipn rejected for %s: %s", order.order_code, exc)
        return {"success": False, "error": str(exc)}, 400
    return "", 204
