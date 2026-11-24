"""Add-on tests on already collected samples, send-out (outsourced / overseas) reminders and per-test flags.

An add-on never edits a released report. It creates a follow-up order for the same patient and clinic through the
normal reception pipeline, linked to the original order, and only while the original sample is still within the
test's add-on window (default 72 hours, per-test override).

Send-out reminders are derived: every order line whose test is flagged "send-out", whose sample has been collected
and whose result has not been entered yet, gets a due date (sent date or collection date + ETA days).
"""

from __future__ import annotations

import json
from datetime import date, datetime, timedelta

from flask import Blueprint, request

from app.api.reception_workspace.routes import _actor, _client_ip, _dxcon_staff_error
from app.core.audit import write_audit
from app.core.tenant_authorization import AuthorizedTenant, resolve_authorized_tenant
from app.extensions.db import db
from app.models.addon import OrderAddon, SendoutTrack, TestFlag
from app.models.biz_order import BizCollection, BizOrder, BizOrderItem, BizResult, BizResultItem
from app.models.sample_collection import SampleCollection
from app.models.test_catalog import TestCatalog
from app.reception_workspace.auth import reception_api_read, reception_api_write

addons_bp = Blueprint("addons", __name__, url_prefix="/api/v1/reception/workspace")

DEFAULT_ADDON_WINDOW_HOURS = 72
CANDIDATE_LOOKBACK_DAYS = 7
SENDOUT_LOOKBACK_DAYS = 120
DUE_SOON_DAYS = 1


def _clean(value, limit: int) -> str:
    return " ".join(str(value or "").split())[:limit]


def collected_at_of(order: BizOrder) -> datetime | None:
    """When the sample for this order was collected (earliest known time), or None if not collected yet."""
    times = []
    sc = SampleCollection.query.filter_by(order_id=order.id).order_by(SampleCollection.created_at).first()
    if sc is not None and sc.collected_at:
        times.append(sc.collected_at)
    bc = BizCollection.query.filter_by(order_id=order.id).first()
    if bc is not None and bc.received_at:
        times.append(bc.received_at)
    return min(times) if times else None


def _flags(test_ids: list[str]) -> dict[str, TestFlag]:
    if not test_ids:
        return {}
    return {f.test_catalog_id: f for f in TestFlag.query.filter(TestFlag.test_catalog_id.in_(test_ids)).all()}


def window_hours(flag: TestFlag | None) -> int:
    return int(flag.addon_window_hours) if flag is not None and flag.addon_window_hours else DEFAULT_ADDON_WINDOW_HOURS


def evaluate_addon(collected_at: datetime, flag: TestFlag | None, now: datetime) -> tuple[bool, float]:
    """(allowed, hours_left) for one test against the age of the collected sample."""
    left = window_hours(flag) - (now - collected_at).total_seconds() / 3600.0
    return left > 0, round(left, 1)


# ------------------------------------------------------------------ add-ons


@addons_bp.route("/addons/candidates", methods=["GET"])
@reception_api_read
def addon_candidates():
    denied = _dxcon_staff_error()
    if denied is not None:
        return denied
    term = _clean(request.args.get("q"), 60)
    if len(term) < 2:
        return {"success": True, "data": []}, 200
    like = f"%{term}%"
    since = datetime.utcnow() - timedelta(days=CANDIDATE_LOOKBACK_DAYS)
    orders = (
        BizOrder.query.filter(
            BizOrder.status != "cancelled",
            BizOrder.created_at >= since - timedelta(days=30),
            BizOrder.order_code.ilike(like) | BizOrder.patient_name.ilike(like) | BizOrder.patient_code.ilike(like),
        )
        .order_by(BizOrder.created_at.desc())
        .limit(30)
        .all()
    )
    now = datetime.utcnow()
    out = []
    for o in orders:
        collected = collected_at_of(o)
        if collected is None or collected < since:
            continue
        out.append(
            {
                "order_code": o.order_code,
                "patient_name": o.patient_name,
                "patient_code": o.patient_code,
                "status": o.status,
                "collected_at": collected.isoformat(),
                "hours_since_collected": round((now - collected).total_seconds() / 3600.0, 1),
                "tests": [i.test_name for i in o.items],
            }
        )
    return {"success": True, "data": out}, 200


@addons_bp.route("/addons/tests", methods=["GET"])
@reception_api_read
def addon_tests():
    denied = _dxcon_staff_error()
    if denied is not None:
        return denied
    order = BizOrder.query.filter_by(order_code=_clean(request.args.get("order_code"), 50)).first()
    if order is None:
        return {"success": False, "error": "Không tìm thấy đơn."}, 404
    collected = collected_at_of(order)
    term = _clean(request.args.get("q"), 60)
    query = TestCatalog.query
    if term:
        like = f"%{term}%"
        query = query.filter(TestCatalog.code.ilike(like) | TestCatalog.name.ilike(like))
    rows = query.order_by(TestCatalog.name).limit(30).all()
    flags = _flags([t.id for t in rows])
    now = datetime.utcnow()
    already = {i.test_code for i in order.items}
    data = []
    for t in rows:
        flag = flags.get(t.id)
        ok, left = evaluate_addon(collected, flag, now) if collected else (False, 0.0)
        data.append(
            {
                "id": t.id,
                "code": t.code,
                "name": t.name,
                "sample_type": t.sample_type,
                "price": t.price or 0,
                "window_hours": window_hours(flag),
                "hours_left": left,
                "allowed": ok and t.code not in already,
                "already_in_order": t.code in already,
                "is_sendout": bool(flag and flag.is_sendout),
                "sendout_eta_days": flag.sendout_eta_days if flag else None,
            }
        )
    return {"success": True, "data": data}, 200


@addons_bp.route("/orders/<order_code>/addons", methods=["POST"])
@reception_api_write
def addon_create(order_code: str):
    denied = _dxcon_staff_error()
    if denied is not None:
        return denied
    from app.business_engine.service import BusinessEngineError
    from app.reception_workspace.consent import consent_gate_enabled, has_required_consent
    from app.reception_workspace.service import ReceptionWorkspaceError, create_reception_order

    payload = request.get_json(silent=True) or {}
    ids = list(dict.fromkeys(str(i) for i in (payload.get("test_catalog_ids") or [])))
    if not ids or len(ids) > 20:
        return {"success": False, "error": "Vui lòng chọn từ 1 đến 20 xét nghiệm."}, 400
    order = BizOrder.query.filter_by(order_code=order_code).first()
    if order is None or order.status == "cancelled":
        return {"success": False, "error": "Không tìm thấy đơn hoặc đơn đã hủy."}, 404
    collected = collected_at_of(order)
    if collected is None:
        return {"success": False, "error": "Mẫu của đơn này chưa được thu, chưa thể làm thêm xét nghiệm."}, 409
    tests = TestCatalog.query.filter(TestCatalog.id.in_(ids)).all()
    if len(tests) != len(ids):
        return {"success": False, "error": "Có xét nghiệm không tồn tại trong danh mục."}, 400
    flags = _flags(ids)
    now = datetime.utcnow()
    existing_codes = {i.test_code for i in order.items}
    problems = []
    for t in tests:
        if t.code in existing_codes:
            problems.append(f"{t.name}: đã có trong đơn gốc")
            continue
        ok, _ = evaluate_addon(collected, flags.get(t.id), now)
        if not ok:
            problems.append(f"{t.name}: quá {window_hours(flags.get(t.id))} giờ kể từ lúc thu mẫu")
    if problems:
        return {"success": False, "error": "Không thể làm thêm: " + "; ".join(problems)}, 409
    if consent_gate_enabled() and not has_required_consent(order.patient_code):
        return {"success": False, "code": "consent_required",
                "error": "Chưa ghi nhận đồng ý xét nghiệm của bệnh nhân."}, 409
    header_org = request.headers.get("X-Organization-ID") or request.headers.get("X-Organization-Id")
    tenant = resolve_authorized_tenant(requested_organization_id=header_org, require_scope=True)
    if not isinstance(tenant, AuthorizedTenant):
        return tenant
    actor = _actor()
    try:
        result = create_reception_order(
            patient_code=order.patient_code,
            test_catalog_ids=ids,
            note=f"Làm thêm từ mẫu của đơn {order.order_code}",
            actor=actor,
            organization_id=order.organization_id,
            collection_organization_id=tenant.organization_id or header_org,
            source_org_code=order.source_org_code,
            collection_mode="AT_RECEPTION",
        )
    except (ReceptionWorkspaceError, BusinessEngineError) as exc:
        db.session.rollback()
        return {"success": False, "error": str(exc)}, 400
    new_code = (result.get("order") or {}).get("order_code")
    new_order = BizOrder.query.filter_by(order_code=new_code).first()
    if new_order is not None:
        new_order.external_ref = order.order_code[:100]
    db.session.add(
        OrderAddon(
            original_order_code=order.order_code,
            addon_order_code=new_code,
            tests_json=json.dumps([{"id": t.id, "code": t.code, "name": t.name} for t in tests], ensure_ascii=False),
            created_by=(actor or "")[:120] or None,
        )
    )
    write_audit("ORDER_ADDON_CREATED", "BizOrder", f"{order.order_code}->{new_code}", user_email=actor or "SYSTEM", ip_address=_client_ip())
    db.session.commit()
    return {"success": True, "data": {"addon_order_code": new_code, "original_order_code": order.order_code}}, 201


# ------------------------------------------------------------ send-out reminders


def _date_of(value: str | None) -> date | None:
    try:
        return date.fromisoformat(value) if value else None
    except ValueError:
        return None


def sendout_status(due: date, today: date) -> str:
    if due < today:
        return "OVERDUE"
    if (due - today).days <= DUE_SOON_DAYS:
        return "DUE_SOON"
    return "WAITING"


@addons_bp.route("/sendout-reminders", methods=["GET"])
@reception_api_read
def sendout_reminders():
    denied = _dxcon_staff_error()
    if denied is not None:
        return denied
    today = datetime.utcnow().date()
    since = datetime.utcnow() - timedelta(days=SENDOUT_LOOKBACK_DAYS)
    rows = (
        db.session.query(BizOrderItem, BizOrder, TestFlag)
        .join(BizOrder, BizOrder.id == BizOrderItem.order_id)
        .join(TestFlag, TestFlag.test_catalog_id == BizOrderItem.test_catalog_id)
        .filter(TestFlag.is_sendout.is_(True), BizOrder.status != "cancelled", BizOrder.created_at >= since)
        .all()
    )
    tracks = {(t.order_code, t.test_code): t for t in SendoutTrack.query.all()}
    items = []
    for item, order, flag in rows:
        track = tracks.get((order.order_code, item.test_code))
        if track is not None and track.dismissed:
            continue
        entered = (
            db.session.query(BizResultItem.id)
            .join(BizResult, BizResult.id == BizResultItem.result_id)
            .filter(BizResult.order_id == order.id, BizResultItem.test_code == item.test_code)
            .first()
        )
        if entered:
            continue
        collected = collected_at_of(order)
        if collected is None:
            continue  # nothing to chase until the sample exists
        sent = _date_of(track.sent_at) if track else None
        due = _date_of(track.eta_date) if track else None
        if due is None:
            if not flag.sendout_eta_days:
                continue  # no ETA configured: cannot estimate, so no reminder
            due = (sent or collected.date()) + timedelta(days=int(flag.sendout_eta_days))
        items.append(
            {
                "order_code": order.order_code,
                "patient_name": order.patient_name,
                "test_code": item.test_code,
                "test_name": item.test_name,
                "destination": (track.destination if track and track.destination else flag.sendout_destination),
                "collected_at": collected.isoformat(),
                "sent_at": track.sent_at if track else None,
                "eta_date": due.isoformat(),
                "days_left": (due - today).days,
                "status": sendout_status(due, today),
                "note": track.note if track else None,
            }
        )
    items.sort(key=lambda i: i["eta_date"])
    counts = {
        "overdue": sum(1 for i in items if i["status"] == "OVERDUE"),
        "due_soon": sum(1 for i in items if i["status"] == "DUE_SOON"),
        "total": len(items),
    }
    return {"success": True, "data": {"items": items, "counts": counts}}, 200


@addons_bp.route("/sendout-reminders/<order_code>/<test_code>", methods=["POST"])
@reception_api_write
def sendout_update(order_code: str, test_code: str):
    denied = _dxcon_staff_error()
    if denied is not None:
        return denied
    payload = request.get_json(silent=True) or {}
    if BizOrder.query.filter_by(order_code=order_code).first() is None:
        return {"success": False, "error": "Không tìm thấy đơn."}, 404
    track = SendoutTrack.query.filter_by(order_code=order_code, test_code=test_code).first()
    if track is None:
        track = SendoutTrack(order_code=order_code, test_code=test_code)
        db.session.add(track)
    for field in ("sent_at", "eta_date"):
        if field in payload:
            raw = _clean(payload.get(field), 10)
            if raw and _date_of(raw) is None:
                return {"success": False, "error": "Ngày không hợp lệ (YYYY-MM-DD)."}, 400
            setattr(track, field, raw or None)
    if "destination" in payload:
        track.destination = _clean(payload.get("destination"), 120) or None
    if "note" in payload:
        track.note = _clean(payload.get("note"), 300) or None
    if "dismissed" in payload:
        track.dismissed = bool(payload.get("dismissed"))
    actor = _actor()
    track.updated_by = (actor or "")[:120] or None
    db.session.commit()
    return {"success": True}, 200


# ------------------------------------------------------------------ test flags


@addons_bp.route("/test-flags", methods=["GET"])
@reception_api_read
def test_flags_list():
    denied = _dxcon_staff_error()
    if denied is not None:
        return denied
    term = _clean(request.args.get("q"), 60)
    query = TestCatalog.query
    if term:
        like = f"%{term}%"
        query = query.filter(TestCatalog.code.ilike(like) | TestCatalog.name.ilike(like))
    rows = query.order_by(TestCatalog.name).limit(40).all()
    flags = _flags([t.id for t in rows])
    return {
        "success": True,
        "data": [
            {
                "id": t.id,
                "code": t.code,
                "name": t.name,
                "is_sendout": bool(flags.get(t.id) and flags[t.id].is_sendout),
                "sendout_destination": flags[t.id].sendout_destination if t.id in flags else None,
                "sendout_eta_days": flags[t.id].sendout_eta_days if t.id in flags else None,
                "addon_window_hours": flags[t.id].addon_window_hours if t.id in flags else None,
            }
            for t in rows
        ],
    }, 200


def _opt_int(value, low: int, high: int):
    if value in (None, ""):
        return None, None
    try:
        number = int(value)
    except (TypeError, ValueError):
        return None, "Giá trị số không hợp lệ."
    if number < low or number > high:
        return None, f"Giá trị phải từ {low} đến {high}."
    return number, None


@addons_bp.route("/test-flags/<test_id>", methods=["POST"])
@reception_api_write
def test_flags_set(test_id: str):
    denied = _dxcon_staff_error()
    if denied is not None:
        return denied
    payload = request.get_json(silent=True) or {}
    test = db.session.get(TestCatalog, test_id)
    if test is None:
        return {"success": False, "error": "Không tìm thấy xét nghiệm."}, 404
    eta, err = _opt_int(payload.get("sendout_eta_days"), 1, 120)
    if err:
        return {"success": False, "error": err}, 400
    window, err = _opt_int(payload.get("addon_window_hours"), 1, 24 * 30)
    if err:
        return {"success": False, "error": err}, 400
    is_sendout = bool(payload.get("is_sendout"))
    if is_sendout and eta is None:
        return {"success": False, "error": "Xét nghiệm gửi ngoài cần nhập số ngày trả kết quả dự kiến."}, 400
    flag = db.session.get(TestFlag, test_id) or TestFlag(test_catalog_id=test_id)
    flag.is_sendout = is_sendout
    flag.sendout_destination = _clean(payload.get("sendout_destination"), 120) or None
    flag.sendout_eta_days = eta
    flag.addon_window_hours = window
    actor = _actor()
    flag.updated_by = (actor or "")[:120] or None
    db.session.add(flag)
    write_audit("TEST_FLAGS_UPDATED", "TestCatalog", test.code, user_email=actor or "SYSTEM", ip_address=_client_ip())
    db.session.commit()
    return {"success": True}, 200
