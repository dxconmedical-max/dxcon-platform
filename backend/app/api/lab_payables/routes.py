"""Lab cost prices (giá nhập), order→lab assignment with margin, and payables to labs (công nợ phải trả). DxCon staff only."""

from __future__ import annotations

from datetime import datetime

from flask import Blueprint, Response, request
from sqlalchemy import select

from app.api.reception_workspace.routes import _actor, _client_ip, _dxcon_staff_error
from app.core.xlsx_export import build_xlsx, xlsx_response
from app.clinic_billing.bulk import MAX_UPLOAD_BYTES, apply_bulk, build_template_xlsx, sheet_to_text, template_rows
from app.clinic_billing.logic import parse_date
from app.core.audit import write_audit
from app.executive_platform.auth import executive_api_read, executive_api_write
from app.extensions.db import db
from app.lab_payables.cost import DEFAULT_SCOPE, assign_lab
from app.models.biz_order import BizOrder
from app.models.lab_payables import (
    LabCostPrice,
    LabPartner,
    LabPayableLine,
    LabPayableStatement,
    LabPayment,
    LabRouting,
    OrderLabCost,
)
from app.models.partner_foundation import PartnerOrganization
from app.models.test_catalog import TestCatalog

lab_payables_bp = Blueprint("lab_payables", __name__, url_prefix="/api/v1/reception/workspace/lab-payables")


def _clean(value, limit: int) -> str:
    return " ".join(str(value or "").split())[:limit]


def _money(value) -> float:
    return round(float(value or 0), 2)


def _lab_ids() -> set[str]:
    ids = {r.organization_id for r in LabPartner.query.all()}
    ids |= {o.id for o in PartnerOrganization.query.filter_by(organization_type="LAB").all()}
    return ids


def _lab_or_error(lab_id: str):
    denied = _dxcon_staff_error()
    if denied is not None:
        return None, denied
    org = db.session.get(PartnerOrganization, lab_id)
    if org is None or lab_id not in _lab_ids():
        return None, ({"success": False, "error": "Không tìm thấy phòng xét nghiệm."}, 404)
    return org, None


def _billed_codes() -> set[str]:
    rows = (
        db.session.query(LabPayableLine.order_code)
        .join(LabPayableStatement, LabPayableStatement.id == LabPayableLine.statement_id)
        .filter(LabPayableStatement.status != "void")
        .all()
    )
    return {r[0] for r in rows}


def _unbilled(lab_id: str, start: str | None = None, end: str | None = None):
    """(complete, missing): assigned orders of this lab not yet on a payable statement."""
    q = (
        db.session.query(OrderLabCost, BizOrder)
        .join(BizOrder, BizOrder.order_code == OrderLabCost.order_code)
        .filter(OrderLabCost.lab_organization_id == lab_id, BizOrder.status != "cancelled")
    )
    if start:
        q = q.filter(BizOrder.created_at >= datetime.fromisoformat(start))
    if end:
        q = q.filter(BizOrder.created_at < datetime.fromisoformat(end).replace(hour=23, minute=59, second=59))
    billed = _billed_codes()
    rows = [(c, o) for c, o in q.order_by(BizOrder.created_at).all() if c.order_code not in billed]
    return [r for r in rows if r[0].missing_count == 0], [r for r in rows if r[0].missing_count > 0]


def _summary(lab_id: str) -> dict:
    stmts = LabPayableStatement.query.filter_by(organization_id=lab_id).filter(LabPayableStatement.status != "void").all()
    billed = sum(s.total_amount for s in stmts)
    paid = sum(p.amount for p in LabPayment.query.filter_by(organization_id=lab_id))
    ok, missing = _unbilled(lab_id)
    return {
        "billed": _money(billed),
        "paid": _money(paid),
        "outstanding": _money(billed - paid),
        "unbilled_orders": len(ok),
        "unbilled_cost": _money(sum(c.cost_total for c, _ in ok)),
        "unbilled_margin": _money(sum(c.sell_total - c.cost_total for c, _ in ok)),
        "missing_cost_orders": len(missing),
    }


# --------------------------------------------------------------------- labs & routing


@lab_payables_bp.route("/labs", methods=["GET"])
@executive_api_read
def labs_overview():
    denied = _dxcon_staff_error()
    if denied is not None:
        return denied
    ids = _lab_ids()
    orgs = PartnerOrganization.query.filter(PartnerOrganization.id.in_(list(ids) or [""])).order_by(PartnerOrganization.organization_name).all()
    data = [{"organization_id": o.id, "organization_name": o.organization_name, "code": o.organization_code, **_summary(o.id)} for o in orgs]
    return {
        "success": True,
        "data": {"labs": data, "total_outstanding": _money(sum(r["outstanding"] for r in data)), "total_unbilled": _money(sum(r["unbilled_cost"] for r in data))},
    }, 200


@lab_payables_bp.route("/organizations", methods=["GET"])
@executive_api_read
def organization_search():
    denied = _dxcon_staff_error()
    if denied is not None:
        return denied
    term = _clean(request.args.get("q"), 60)
    q = PartnerOrganization.query
    if term:
        like = f"%{term}%"
        q = q.filter(PartnerOrganization.organization_name.ilike(like) | PartnerOrganization.organization_code.ilike(like))
    rows = q.order_by(PartnerOrganization.organization_name).limit(20).all()
    return {
        "success": True,
        "data": [{"id": o.id, "name": o.organization_name, "code": o.organization_code, "type": o.organization_type} for o in rows],
    }, 200


@lab_payables_bp.route("/labs", methods=["POST"])
@executive_api_write
def lab_add():
    denied = _dxcon_staff_error()
    if denied is not None:
        return denied
    org_id = _clean((request.get_json(silent=True) or {}).get("organization_id"), 36)
    org = db.session.get(PartnerOrganization, org_id) if org_id else None
    if org is None:
        return {"success": False, "error": "Không tìm thấy đơn vị."}, 404
    if org.id not in _lab_ids():
        db.session.add(LabPartner(organization_id=org.id, created_by=(_actor() or "")[:120] or None))
        write_audit("LAB_PARTNER_ADDED", "PartnerOrganization", org.organization_code, user_email=_actor() or "SYSTEM", ip_address=_client_ip())
        db.session.commit()
    return {"success": True, "data": {"organization_id": org.id}}, 201


@lab_payables_bp.route("/routing", methods=["GET"])
@executive_api_read
def routing_get():
    denied = _dxcon_staff_error()
    if denied is not None:
        return denied
    labs = {o.id: o.organization_name for o in PartnerOrganization.query.filter(PartnerOrganization.id.in_(list(_lab_ids()) or [""])).all()}
    routes = {r.scope_org_id: r.lab_organization_id for r in LabRouting.query.all()}
    clinics = PartnerOrganization.query.filter_by(organization_type="CLINIC").order_by(PartnerOrganization.organization_name).all()
    default = routes.get(DEFAULT_SCOPE)
    return {
        "success": True,
        "data": {
            "labs": [{"id": k, "name": v} for k, v in labs.items()],
            "default_lab_id": default,
            "clinics": [{"id": c.id, "name": c.organization_name, "lab_id": routes.get(c.id)} for c in clinics],
        },
    }, 200


@lab_payables_bp.route("/routing", methods=["POST"])
@executive_api_write
def routing_set():
    denied = _dxcon_staff_error()
    if denied is not None:
        return denied
    body = request.get_json(silent=True) or {}
    scope = _clean(body.get("scope_org_id"), 36)
    lab_id = _clean(body.get("lab_organization_id"), 36)
    if scope != DEFAULT_SCOPE and (not scope or db.session.get(PartnerOrganization, scope) is None):
        return {"success": False, "error": "Không tìm thấy phòng khám."}, 404
    row = db.session.get(LabRouting, scope)
    if not lab_id:  # clear
        if row is not None:
            db.session.delete(row)
            db.session.commit()
        return {"success": True}, 200
    if lab_id not in _lab_ids():
        return {"success": False, "error": "Đơn vị này chưa được thêm làm phòng xét nghiệm."}, 400
    if row is None:
        db.session.add(LabRouting(scope_org_id=scope, lab_organization_id=lab_id, updated_by=(_actor() or "")[:120] or None))
    else:
        row.lab_organization_id = lab_id
        row.updated_by = (_actor() or "")[:120] or None
    db.session.commit()
    return {"success": True}, 200


@lab_payables_bp.route("/unassigned", methods=["GET"])
@executive_api_read
def unassigned_orders():
    denied = _dxcon_staff_error()
    if denied is not None:
        return denied
    assigned = select(OrderLabCost.order_code)
    rows = (
        BizOrder.query.filter(BizOrder.status != "cancelled", ~BizOrder.order_code.in_(assigned))
        .order_by(BizOrder.created_at.desc())
        .limit(100)
        .all()
    )
    orgs = {o.id: o.organization_name for o in PartnerOrganization.query.filter(PartnerOrganization.id.in_([r.organization_id for r in rows if r.organization_id] or [""])).all()}
    return {
        "success": True,
        "data": [
            {
                "order_code": o.order_code,
                "patient_name": o.patient_name,
                "clinic_name": orgs.get(o.organization_id) or "Khách vãng lai",
                "total_amount": o.total_amount,
                "created_at": o.created_at.isoformat() if o.created_at else None,
            }
            for o in rows
        ],
    }, 200


@lab_payables_bp.route("/orders/assign", methods=["POST"])
@executive_api_write
def orders_assign():
    denied = _dxcon_staff_error()
    if denied is not None:
        return denied
    body = request.get_json(silent=True) or {}
    lab_id = _clean(body.get("lab_organization_id"), 36)
    if lab_id not in _lab_ids():
        return {"success": False, "error": "Chưa chọn phòng xét nghiệm hợp lệ."}, 400
    codes = [_clean(c, 50) for c in (body.get("order_codes") or [])][:200]
    done = frozen = 0
    for code in codes:
        order = BizOrder.query.filter_by(order_code=code).first()
        if order is None:
            continue
        if assign_lab(order, lab_id, _actor()) is None:
            frozen += 1
        else:
            done += 1
    db.session.commit()
    return {"success": True, "data": {"assigned": done, "locked": frozen}}, 200


# --------------------------------------------------------------------- profit report


def _profit_range():
    today = datetime.utcnow().date()
    start = parse_date(_clean(request.args.get("start"), 10)) or today.replace(day=1)
    end = parse_date(_clean(request.args.get("end"), 10)) or today
    return start, end


def _profit_data(start, end) -> dict:
    rows = (
        db.session.query(OrderLabCost, BizOrder)
        .join(BizOrder, BizOrder.order_code == OrderLabCost.order_code)
        .filter(
            BizOrder.status != "cancelled",
            BizOrder.created_at >= datetime.combine(start, datetime.min.time()),
            BizOrder.created_at < datetime.combine(end, datetime.min.time()).replace(hour=23, minute=59, second=59),
        )
        .all()
    )
    ids = {o.organization_id for _, o in rows if o.organization_id} | {c.lab_organization_id for c, _ in rows}
    names = {o.id: o.organization_name for o in PartnerOrganization.query.filter(PartnerOrganization.id.in_(list(ids) or [""])).all()}

    def blank(label: str) -> dict:
        return {"label": label, "orders": 0, "sell": 0.0, "cost": 0.0, "margin": 0.0, "margin_pct": 0.0, "missing_cost_orders": 0}

    def add(bucket: dict, cost_row, order) -> None:
        if cost_row.missing_count > 0:
            bucket["missing_cost_orders"] += 1
            return
        bucket["orders"] += 1
        bucket["sell"] += cost_row.sell_total
        bucket["cost"] += cost_row.cost_total

    total = blank("Tổng")
    groups: dict[str, dict[str, dict]] = {"clinic": {}, "lab": {}, "month": {}}
    for c, o in rows:
        add(total, c, o)
        keys = {
            "clinic": names.get(o.organization_id) or "Khách vãng lai",
            "lab": names.get(c.lab_organization_id) or c.lab_organization_id,
            "month": o.created_at.strftime("%Y-%m") if o.created_at else "—",
        }
        for kind, label in keys.items():
            add(groups[kind].setdefault(label, blank(label)), c, o)

    def finish(b: dict) -> dict:
        b["sell"], b["cost"] = _money(b["sell"]), _money(b["cost"])
        b["margin"] = _money(b["sell"] - b["cost"])
        b["margin_pct"] = round(b["margin"] / b["sell"] * 100, 1) if b["sell"] else 0.0
        return b

    def listing(kind: str) -> list[dict]:
        out = [finish(b) for b in groups[kind].values()]
        return sorted(out, key=(lambda b: b["label"]) if kind == "month" else (lambda b: -b["margin"]))

    return {
        "start": start.isoformat(),
        "end": end.isoformat(),
        "total": finish(total),
        "by_clinic": listing("clinic"),
        "by_lab": listing("lab"),
        "by_month": listing("month"),
    }


@lab_payables_bp.route("/profit", methods=["GET"])
@executive_api_read
def profit_report():
    """Margin = sell - cost over orders assigned to a lab. Orders missing a cost price are counted apart."""
    denied = _dxcon_staff_error()
    if denied is not None:
        return denied
    start, end = _profit_range()
    if end < start:
        return {"success": False, "error": "Khoảng ngày không hợp lệ."}, 400
    return {"success": True, "data": _profit_data(start, end)}, 200


@lab_payables_bp.route("/profit/export", methods=["GET"])
@executive_api_read
def profit_export():
    denied = _dxcon_staff_error()
    if denied is not None:
        return denied
    start, end = _profit_range()
    if end < start:
        return {"success": False, "error": "Khoảng ngày không hợp lệ."}, 400
    d = _profit_data(start, end)
    head = ["Nhóm", "Số đơn", "Doanh thu", "Giá vốn", "Lãi", "Lãi %", "Đơn thiếu giá nhập"]

    def line(b: dict) -> list:
        return [b["label"], b["orders"], b["sell"], b["cost"], b["margin"], b["margin_pct"], b["missing_cost_orders"]]

    sheets = [
        ("Tổng", head, [line(d["total"])]),
        ("Theo phòng khám", head, [line(b) for b in d["by_clinic"]]),
        ("Theo phòng xét nghiệm", head, [line(b) for b in d["by_lab"]]),
        ("Theo tháng", head, [line(b) for b in d["by_month"]]),
    ]
    money = {t: {2, 3, 4} for t, _, _ in sheets}
    return xlsx_response(build_xlsx(sheets, money), f"bao-cao-lai-{d['start']}-{d['end']}")


# --------------------------------------------------------------------- one lab


@lab_payables_bp.route("/<lab_id>", methods=["GET"])
@executive_api_read
def lab_overview(lab_id: str):
    lab, err = _lab_or_error(lab_id)
    if err is not None:
        return err
    stmts = LabPayableStatement.query.filter_by(organization_id=lab_id).order_by(LabPayableStatement.period_start.desc()).all()
    pays = LabPayment.query.filter_by(organization_id=lab_id).order_by(LabPayment.paid_at.desc()).limit(50).all()
    return {
        "success": True,
        "data": {
            "lab": {"id": lab.id, "name": lab.organization_name, "code": lab.organization_code},
            "summary": _summary(lab_id),
            "statements": [
                {
                    "id": s.id,
                    "statement_no": s.statement_no,
                    "period_start": s.period_start,
                    "period_end": s.period_end,
                    "order_count": s.order_count,
                    "total_amount": s.total_amount,
                    "status": s.status,
                    "note": s.note,
                }
                for s in stmts
            ],
            "payments": [
                {"id": p.id, "amount": p.amount, "paid_at": p.paid_at, "method": p.method, "reference": p.reference, "note": p.note}
                for p in pays
            ],
        },
    }, 200


@lab_payables_bp.route("/<lab_id>/costs", methods=["GET"])
@executive_api_read
def list_costs(lab_id: str):
    lab, err = _lab_or_error(lab_id)
    if err is not None:
        return err
    term = _clean(request.args.get("q"), 60)
    only = request.args.get("custom") == "1"
    query = TestCatalog.query
    if term:
        like = f"%{term}%"
        query = query.filter(TestCatalog.code.ilike(like) | TestCatalog.name.ilike(like))
    costs = {c.test_catalog_id: c.cost for c in LabCostPrice.query.filter_by(organization_id=lab_id)}
    if only:
        query = query.filter(TestCatalog.id.in_(list(costs) or [""]))
    rows = query.order_by(TestCatalog.name).limit(40).all()
    return {
        "success": True,
        "data": {
            "priced_count": len(costs),
            "tests": [{"id": t.id, "code": t.code, "name": t.name, "list_price": t.price or 0, "cost": costs.get(t.id)} for t in rows],
        },
    }, 200


def _bulk_response(text: str, lab_id: str, lab, apply: bool):
    result, msg = apply_bulk(text, lab_id, LabCostPrice, "cost", (_actor() or "")[:120] or None, apply)
    if msg:
        return {"success": False, "error": msg}, 400
    if apply and result["changed"]:
        write_audit("LAB_COST_BULK", "PartnerOrganization", lab.organization_code, user_email=_actor() or "SYSTEM", ip_address=_client_ip())
        db.session.commit()
    result.pop("changed", None)
    return {"success": True, "data": result}, 200


@lab_payables_bp.route("/<lab_id>/costs/bulk", methods=["POST"])
@executive_api_write
def costs_bulk(lab_id: str):
    lab, err = _lab_or_error(lab_id)
    if err is not None:
        return err
    body = request.get_json(silent=True) or {}
    return _bulk_response(str(body.get("text") or ""), lab_id, lab, body.get("apply") is True)


@lab_payables_bp.route("/<lab_id>/costs/template", methods=["GET"])
@executive_api_read
def costs_template(lab_id: str):
    lab, err = _lab_or_error(lab_id)
    if err is not None:
        return err
    current = {c.test_catalog_id: c.cost for c in LabCostPrice.query.filter_by(organization_id=lab_id)}
    data = build_template_xlsx("Giá nhập từ phòng xét nghiệm (điền)", template_rows(current))
    return Response(
        data,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="gia-nhap-{lab.organization_code}.xlsx"'},
    )


@lab_payables_bp.route("/<lab_id>/costs/upload", methods=["POST"])
@executive_api_write
def costs_upload(lab_id: str):
    lab, err = _lab_or_error(lab_id)
    if err is not None:
        return err
    f = request.files.get("file")
    if f is None or not f.filename:
        return {"success": False, "error": "Chưa chọn file."}, 400
    data = f.read(MAX_UPLOAD_BYTES + 1)
    if len(data) > MAX_UPLOAD_BYTES:
        return {"success": False, "error": "File quá lớn (tối đa 2MB)."}, 413
    try:
        text = sheet_to_text(f.filename, data)
    except Exception:
        return {"success": False, "error": "Không đọc được file. Hãy dùng file Excel (.xlsx) hoặc CSV theo biểu mẫu."}, 400
    return _bulk_response(text, lab_id, lab, request.form.get("apply") == "1")


@lab_payables_bp.route("/<lab_id>/recalc", methods=["POST"])
@executive_api_write
def recalc_orders(lab_id: str):
    """Re-apply current cost prices to this lab's orders that are not yet on a statement (e.g. after loading prices)."""
    lab, err = _lab_or_error(lab_id)
    if err is not None:
        return err
    ok, missing = _unbilled(lab_id)
    n = 0
    for c, o in ok + missing:
        if assign_lab(o, lab_id, _actor()) is not None:
            n += 1
    db.session.commit()
    return {"success": True, "data": {"recalculated": n}}, 200


def _period(body: dict):
    ds, de = parse_date(_clean(body.get("period_start"), 10)), parse_date(_clean(body.get("period_end"), 10))
    if ds is None or de is None or de < ds:
        return None, None, "Kỳ đối soát không hợp lệ (từ ngày – đến ngày, định dạng YYYY-MM-DD)."
    return ds, de, None


@lab_payables_bp.route("/<lab_id>/statements/preview", methods=["POST"])
@executive_api_write
def statement_preview(lab_id: str):
    lab, err = _lab_or_error(lab_id)
    if err is not None:
        return err
    ds, de, msg = _period(request.get_json(silent=True) or {})
    if msg:
        return {"success": False, "error": msg}, 400
    ok, missing = _unbilled(lab_id, ds.isoformat(), de.isoformat())
    return {
        "success": True,
        "data": {
            "order_count": len(ok),
            "total_amount": _money(sum(c.cost_total for c, _ in ok)),
            "margin": _money(sum(c.sell_total - c.cost_total for c, _ in ok)),
            "missing_cost_orders": len(missing),
        },
    }, 200


@lab_payables_bp.route("/<lab_id>/statements", methods=["POST"])
@executive_api_write
def statement_create(lab_id: str):
    lab, err = _lab_or_error(lab_id)
    if err is not None:
        return err
    body = request.get_json(silent=True) or {}
    ds, de, msg = _period(body)
    if msg:
        return {"success": False, "error": msg}, 400
    ok, _missing = _unbilled(lab_id, ds.isoformat(), de.isoformat())
    if not ok:
        return {"success": False, "error": "Không có ca nào (đủ giá nhập) chưa đối soát trong kỳ này."}, 409
    count = LabPayableStatement.query.filter_by(organization_id=lab_id).count() + 1
    no = f"PT-{lab.organization_code}-{de.strftime('%Y%m')}-{count:02d}"
    while LabPayableStatement.query.filter_by(statement_no=no[:40]).first() is not None:
        count += 1
        no = f"PT-{lab.organization_code}-{de.strftime('%Y%m')}-{count:02d}"
    stmt = LabPayableStatement(
        organization_id=lab_id,
        statement_no=no[:40],
        period_start=ds.isoformat(),
        period_end=de.isoformat(),
        order_count=len(ok),
        total_amount=_money(sum(c.cost_total for c, _ in ok)),
        note=_clean(body.get("note"), 300) or None,
        created_by=(_actor() or "")[:120] or None,
    )
    db.session.add(stmt)
    db.session.flush()
    for c, _o in ok:
        db.session.add(LabPayableLine(statement_id=stmt.id, order_code=c.order_code, amount=_money(c.cost_total)))
    write_audit("LAB_STATEMENT_CREATED", "LabPayableStatement", stmt.statement_no, user_email=_actor() or "SYSTEM", ip_address=_client_ip())
    db.session.commit()
    return {"success": True, "data": {"id": stmt.id, "statement_no": stmt.statement_no, "total_amount": stmt.total_amount}}, 201


@lab_payables_bp.route("/<lab_id>/statements/<statement_id>", methods=["GET"])
@executive_api_read
def statement_detail(lab_id: str, statement_id: str):
    lab, err = _lab_or_error(lab_id)
    if err is not None:
        return err
    stmt = LabPayableStatement.query.filter_by(id=statement_id, organization_id=lab_id).first()
    if stmt is None:
        return {"success": False, "error": "Không tìm thấy bảng đối soát."}, 404
    lines = LabPayableLine.query.filter_by(statement_id=stmt.id).all()
    orders = {o.order_code: o for o in BizOrder.query.filter(BizOrder.order_code.in_([l.order_code for l in lines] or [""])).all()}
    return {
        "success": True,
        "data": {
            "statement_no": stmt.statement_no,
            "lab_name": lab.organization_name,
            "period_start": stmt.period_start,
            "period_end": stmt.period_end,
            "total_amount": stmt.total_amount,
            "status": stmt.status,
            "lines": [
                {
                    "order_code": l.order_code,
                    "patient_name": orders[l.order_code].patient_name if l.order_code in orders else "",
                    "amount": l.amount,
                }
                for l in lines
            ],
        },
    }, 200


@lab_payables_bp.route("/<lab_id>/statements/<statement_id>/export", methods=["GET"])
@executive_api_read
def statement_export(lab_id: str, statement_id: str):
    lab, err = _lab_or_error(lab_id)
    if err is not None:
        return err
    stmt = LabPayableStatement.query.filter_by(id=statement_id, organization_id=lab_id).first()
    if stmt is None:
        return {"success": False, "error": "Không tìm thấy bảng đối soát."}, 404
    lines = LabPayableLine.query.filter_by(statement_id=stmt.id).all()
    orders = {o.order_code: o for o in BizOrder.query.filter(BizOrder.order_code.in_([l.order_code for l in lines] or [""])).all()}
    rows = [[l.order_code, orders[l.order_code].patient_name if l.order_code in orders else "", l.amount] for l in lines]
    rows.append(["", "TỔNG CỘNG", stmt.total_amount])
    head = ["Mã đơn", "Bệnh nhân", "Phải trả phòng xét nghiệm"]
    title = f"{lab.organization_name} · {stmt.period_start} → {stmt.period_end} · {stmt.status}"
    data = build_xlsx([("Đối soát", head, rows), ("Thông tin", ["Mục", "Giá trị"], [["Số bảng", stmt.statement_no], ["Phòng xét nghiệm", title]])], {"Đối soát": {2}})
    return xlsx_response(data, f"doi-soat-{stmt.statement_no}")


@lab_payables_bp.route("/<lab_id>/statements/<statement_id>/void", methods=["POST"])
@executive_api_write
def statement_void(lab_id: str, statement_id: str):
    lab, err = _lab_or_error(lab_id)
    if err is not None:
        return err
    stmt = LabPayableStatement.query.filter_by(id=statement_id, organization_id=lab_id).first()
    if stmt is None:
        return {"success": False, "error": "Không tìm thấy bảng đối soát."}, 404
    if LabPayment.query.filter_by(organization_id=lab_id).count():
        return {"success": False, "error": "Đã có khoản chuyển cho phòng xét nghiệm này nên không hủy được bảng đối soát."}, 409
    LabPayableLine.query.filter_by(statement_id=stmt.id).delete()
    stmt.status = "void"
    write_audit("LAB_STATEMENT_VOIDED", "LabPayableStatement", stmt.statement_no, user_email=_actor() or "SYSTEM", ip_address=_client_ip())
    db.session.commit()
    return {"success": True}, 200


@lab_payables_bp.route("/<lab_id>/payments", methods=["POST"])
@executive_api_write
def payment_add(lab_id: str):
    lab, err = _lab_or_error(lab_id)
    if err is not None:
        return err
    body = request.get_json(silent=True) or {}
    try:
        amount = float(body.get("amount"))
    except (TypeError, ValueError):
        return {"success": False, "error": "Số tiền không hợp lệ."}, 400
    paid_at = parse_date(_clean(body.get("paid_at"), 10))
    if amount <= 0 or paid_at is None:
        return {"success": False, "error": "Cần số tiền lớn hơn 0 và ngày chuyển (YYYY-MM-DD)."}, 400
    row = LabPayment(
        organization_id=lab_id,
        amount=_money(amount),
        paid_at=paid_at.isoformat(),
        method=_clean(body.get("method"), 40) or None,
        reference=_clean(body.get("reference"), 120) or None,
        note=_clean(body.get("note"), 300) or None,
        created_by=(_actor() or "")[:120] or None,
    )
    db.session.add(row)
    write_audit("LAB_PAYMENT_ADDED", "PartnerOrganization", lab.organization_code, user_email=_actor() or "SYSTEM", ip_address=_client_ip())
    db.session.commit()
    return {"success": True, "data": {"id": row.id}}, 201
