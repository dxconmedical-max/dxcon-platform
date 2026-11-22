import threading
import time

from flask import Blueprint, current_app, request

from app.business_engine.statuses import RESULT_RELEASED
from app.core.audit import write_audit
from app.core.authenticated_identity import authenticated_actor_email, get_authenticated_identity
from app.core.authz import roles_required
from app.core.patient_scope import is_internal_org
from app.extensions.db import db
from app.models.biz_order import BizOrder, BizResult
from app.services import result_links

result_links_bp = Blueprint("result_links", __name__, url_prefix="/api/v1")

_ANY_ORG = ("SUPER_ADMIN", "SYSTEM_ADMIN")
_INTERNAL = ("ADMIN", "RECEPTION")
_NOT_FOUND = {"success": False, "error": "Link không hợp lệ hoặc đã hết hạn."}

_PER_MINUTE = 30
_hits_lock = threading.Lock()
_hits: dict[str, list[float]] = {}


def _client_ip() -> str:
    forwarded = request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
    return (forwarded or request.remote_addr or "")[:100]


def _rate_limited(ip: str) -> bool:
    now = time.time()
    with _hits_lock:
        recent = [t for t in _hits.get(ip, []) if now - t < 60]
        recent.append(now)
        _hits[ip] = recent
        if len(_hits) > 5000:
            for key in [k for k, v in _hits.items() if not v or now - v[-1] > 60]:
                _hits.pop(key, None)
        return len(recent) > _PER_MINUTE


def _released_result(order_code: str):
    order = BizOrder.query.filter_by(order_code=order_code).first()
    if not order:
        return None, None
    result = BizResult.query.filter_by(order_id=order.id).first()
    if (
        not result
        or (result.status or "").lower() != RESULT_RELEASED
        or not result.patient_visible
        or not result.released_at
    ):
        return order, None
    return order, result


@result_links_bp.route("/result-links/<order_code>", methods=["POST"])
@roles_required(*_ANY_ORG, *_INTERNAL)
def create_link(order_code):
    identity = get_authenticated_identity()
    if identity.platform_role not in _ANY_ORG and not is_internal_org(identity.organization_id):
        return {"success": False, "error": "DxCon staff only"}, 403
    order, result = _released_result(order_code)
    if not order:
        return {"success": False, "error": "order not found"}, 404
    if not result:
        return {
            "success": False,
            "error": "Kết quả chưa được duyệt và phát hành, chưa thể tạo link.",
        }, 409

    token = result_links.make_token(order.order_code, result.released_at)
    base = (current_app.config.get("PUBLIC_SITE_URL") or "https://dxcon.com.vn").rstrip("/")
    url = f"{base}/r/{token}"

    qr_png = None
    try:
        from app.reception_workspace.qr_engine import render_qr_png_data_url

        qr_png = render_qr_png_data_url(url)
    except Exception:
        qr_png = None

    write_audit(
        action="RESULT_LINK_CREATED",
        object_type="ORDER",
        object_id=order.order_code,
        user_email=authenticated_actor_email(),
        ip_address=_client_ip(),
    )
    db.session.commit()
    return {
        "success": True,
        "url": url,
        "qr_png": qr_png,
        "expires_days": result_links.MAX_AGE_SECONDS // 86400,
    }


@result_links_bp.route("/public/results/<token>", methods=["GET"])
def public_result(token):
    if _rate_limited(_client_ip()):
        return {"success": False, "error": "Quá nhiều yêu cầu, vui lòng thử lại sau."}, 429

    data = result_links.read_token(token)
    if not data:
        return _NOT_FOUND, 404
    order, result = _released_result(data["o"])
    if not result or result_links.release_stamp(result.released_at) != data["r"]:
        return _NOT_FOUND, 404

    write_audit(
        action="RESULT_LINK_OPENED",
        object_type="ORDER",
        object_id=order.order_code,
        user_email="patient-link",
        ip_address=_client_ip(),
    )
    db.session.commit()
    body = {
        "success": True,
        "patient_name": order.patient_name,
        "order_code": order.order_code,
        "released_at": result.released_at.isoformat() + "Z",
        "items": [
            {
                "test_name": i.test_name,
                "result_value": i.result_value,
                "unit": i.unit,
                "reference_range": i.reference_range,
                "flag": i.flag,
            }
            for i in result.items
        ],
    }
    return body, 200, {"Cache-Control": "no-store", "X-Robots-Tag": "noindex"}
