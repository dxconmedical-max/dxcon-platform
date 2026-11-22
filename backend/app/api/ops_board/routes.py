from datetime import date, datetime, timedelta

from flask import Blueprint, current_app, request
from sqlalchemy import func

from app.core.authenticated_identity import get_authenticated_identity
from app.core.authz import roles_required
from app.core.patient_scope import is_internal_org
from app.extensions.db import db
from app.models.biz_order import BizOrder, BizPayment
from app.models.sample_collection import SampleCollection
from app.services import live_location_store

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


def _staff_gate():
    identity = get_authenticated_identity()
    if identity.platform_role not in _ANY_ORG and not is_internal_org(identity.organization_id):
        return {"success": False, "error": "DxCon staff only"}, 403
    return None


_FIELD_MODES = ("HOME_COLLECTION", "CLINIC_COLLECTION")


@ops_board_bp.route("/collections", methods=["GET"])
@roles_required(*_ANY_ORG, *_INTERNAL)
def collections_board():
    denied = _staff_gate()
    if denied:
        return denied
    status = (request.args.get("status") or "").strip().upper()
    query = SampleCollection.query.filter(SampleCollection.collection_mode.in_(_FIELD_MODES))
    if status:
        query = query.filter(func.upper(SampleCollection.status) == status)
    rows = query.order_by(SampleCollection.created_at.desc()).limit(200).all()

    order_ids = [r.order_id for r in rows if r.order_id]
    orders = {}
    if order_ids:
        orders = {o.id: o for o in BizOrder.query.filter(BizOrder.id.in_(order_ids)).all()}
    live = {i["user_id"]: i for i in live_location_store.list_all(current_app._get_current_object())}

    items = []
    by_status = {}
    unassigned = 0
    for r in rows:
        st = (r.status or "").upper()
        by_status[st] = by_status.get(st, 0) + 1
        if not r.collector_id:
            unassigned += 1
        order = orders.get(r.order_id)
        ping = live.get(r.collector_id) if r.collector_id else None
        items.append(
            {
                "id": r.id,
                "order_code": order.order_code if order else None,
                "patient_name": (order.patient_name if order else None) or r.contact_person,
                "contact_phone": r.contact_phone,
                "address": r.pickup_address,
                "requested_date": r.requested_date,
                "time_window": r.requested_time_window,
                "status": st,
                "collector_id": r.collector_id,
                "collector_name": r.collector_name,
                "collector_online": ping is not None,
                "collector_last_seen": ping["recorded_at"] if ping else None,
                "created_at": r.created_at.isoformat() + "Z" if r.created_at else None,
            }
        )
    return {
        "success": True,
        "items": items,
        "summary": {"total": len(items), "unassigned": unassigned, "by_status": by_status},
    }


@ops_board_bp.route("/report", methods=["GET"])
@roles_required(*_ANY_ORG, *_INTERNAL)
def daily_report():
    denied = _staff_gate()
    if denied:
        return denied
    today = (datetime.utcnow() + _VN_OFFSET).date()
    day_to = _parse_day(request.args.get("date_to")) or today
    day_from = _parse_day(request.args.get("date_from")) or (day_to - timedelta(days=13))
    if day_from > day_to:
        day_from, day_to = day_to, day_from
    if (day_to - day_from).days > 92:
        day_from = day_to - timedelta(days=92)
    start = _utc_start(day_from)
    end = _utc_start(day_to) + timedelta(days=1)

    days = {}
    cur = day_from
    while cur <= day_to:
        days[cur.isoformat()] = {"date": cur.isoformat(), "orders": 0, "orders_value": 0.0, "collected": 0.0}
        cur += timedelta(days=1)

    def _vn_day(ts):
        return (ts + _VN_OFFSET).date().isoformat()

    for created, total, st in (
        db.session.query(BizOrder.created_at, BizOrder.total_amount, BizOrder.status)
        .filter(BizOrder.created_at >= start, BizOrder.created_at < end)
        .all()
    ):
        if created is None or (st or "").lower() == "cancelled":
            continue
        row = days.get(_vn_day(created))
        if row:
            row["orders"] += 1
            row["orders_value"] += float(total or 0)
    for paid_at, amount in (
        db.session.query(BizPayment.paid_at, BizPayment.amount)
        .filter(BizPayment.paid_at >= start, BizPayment.paid_at < end)
        .all()
    ):
        if paid_at is None:
            continue
        row = days.get(_vn_day(paid_at))
        if row:
            row["collected"] += float(amount or 0)

    series = list(days.values())
    return {
        "success": True,
        "days": series,
        "totals": {
            "orders": sum(d["orders"] for d in series),
            "orders_value": sum(d["orders_value"] for d in series),
            "collected": sum(d["collected"] for d in series),
        },
        "date_from": day_from.isoformat(),
        "date_to": day_to.isoformat(),
    }
