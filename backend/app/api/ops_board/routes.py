from datetime import date, datetime, timedelta

from flask import Blueprint, request
from sqlalchemy import func

from app.core.authenticated_identity import get_authenticated_identity
from app.core.authz import roles_required
from app.core.patient_scope import is_internal_org
from app.extensions.db import db
from app.models.biz_order import BizOrder, BizPayment

ops_board_bp = Blueprint("ops_board", __name__, url_prefix="/api/v1/ops-board")

_ANY_ORG = ("SUPER_ADMIN", "SYSTEM_ADMIN")
_INTERNAL = ("ADMIN", "RECEPTION", "ACCOUNTING")
_VN_OFFSET = timedelta(hours=7)
_PAGE_SIZE = 100


def _parse_day(value):
    if not value:
        return None
    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError:
        return None


def _utc_start(day):
    return datetime(day.year, day.month, day.day) - _VN_OFFSET


@ops_board_bp.route("/orders", methods=["GET"])
@roles_required(*_ANY_ORG, *_INTERNAL)
def orders_board():
    identity = get_authenticated_identity()
    if identity.platform_role not in _ANY_ORG and not is_internal_org(identity.organization_id):
        return {"success": False, "error": "DxCon staff only"}, 403

    status = (request.args.get("status") or "").strip().lower()
    q = (request.args.get("q") or "").strip()
    day_from = _parse_day(request.args.get("date_from"))
    day_to = _parse_day(request.args.get("date_to"))
    try:
        page = max(1, int(request.args.get("page", 1)))
    except ValueError:
        page = 1

    scope = []
    if day_from:
        scope.append(BizOrder.created_at >= _utc_start(day_from))
    if day_to:
        scope.append(BizOrder.created_at < _utc_start(day_to) + timedelta(days=1))
    if q:
        like = f"%{q}%"
        scope.append(db.or_(BizOrder.order_code.ilike(like), BizOrder.patient_name.ilike(like)))

    listing = db.session.query(BizOrder).filter(*scope)
    if status:
        listing = listing.filter(func.lower(BizOrder.status) == status)
    total_rows = listing.count()
    rows = (
        listing.order_by(BizOrder.created_at.desc())
        .offset((page - 1) * _PAGE_SIZE)
        .limit(_PAGE_SIZE)
        .all()
    )

    by_status = {
        (s or "").lower(): int(n)
        for s, n in db.session.query(BizOrder.status, func.count(BizOrder.id))
        .filter(*scope)
        .group_by(BizOrder.status)
        .all()
    }
    order_total = (
        db.session.query(func.coalesce(func.sum(BizOrder.total_amount), 0)).filter(*scope).scalar()
    )

    pay_scope = []
    if day_from:
        pay_scope.append(BizPayment.paid_at >= _utc_start(day_from))
    if day_to:
        pay_scope.append(BizPayment.paid_at < _utc_start(day_to) + timedelta(days=1))
    collected = (
        db.session.query(func.coalesce(func.sum(BizPayment.amount), 0)).filter(*pay_scope).scalar()
    )

    return {
        "success": True,
        "orders": [
            {
                "order_code": o.order_code,
                "patient_name": o.patient_name,
                "status": (o.status or "").lower(),
                "total_amount": float(o.total_amount or 0),
                "created_at": o.created_at.isoformat() + "Z" if o.created_at else None,
                "source_org_name": o.source_org_name_raw,
            }
            for o in rows
        ],
        "total_rows": total_rows,
        "page": page,
        "page_size": _PAGE_SIZE,
        "summary": {
            "orders": sum(by_status.values()),
            "by_status": by_status,
            "orders_value": float(order_total or 0),
            "collected": float(collected or 0),
        },
    }
