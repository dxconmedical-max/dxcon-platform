"""CRM for DxCon sales: customer accounts, contact log, sales targets, market share vs estimated monthly cases.

Admins see everything. A SALE user sees and edits only accounts they own and never sees cost or margin.
"""

from __future__ import annotations

from datetime import datetime

from flask import Blueprint, request, session

from app.api.reception_workspace.routes import _actor, _client_ip
from app.clinic_billing.logic import parse_date
from app.clinic_billing.bulk import MAX_UPLOAD_BYTES
from app.core.audit import write_audit
from app.core.xlsx_export import build_xlsx, xlsx_response
from app.core.authenticated_identity import get_authenticated_identity
from app.executive_platform.auth import _dual
from app.extensions.db import db
from app.models.biz_order import BizOrder
from app.models.crm_sales import ACCOUNT_TYPES, ACTIVITY_KINDS, STAGES, CrmAccount, CrmActivity, CrmSaleTarget
from app.models.lab_payables import OrderLabCost
from app.models.partner_foundation import PartnerOrganization
from app.models.user import User

crm_sales_bp = Blueprint("crm_sales", __name__, url_prefix="/api/v1/reception/workspace/crm")

ADMIN_ROLES = frozenset({"SUPER_ADMIN", "ADMIN"})
CRM_ROLES = ADMIN_ROLES | {"SALE"}


def crm_access(fn):
    return _dual(CRM_ROLES, fn)


def admin_only(fn):
    return _dual(ADMIN_ROLES, fn)


def _clean(value, limit: int) -> str:
    return " ".join(str(value or "").split())[:limit]


def _who():
    """(user_id, is_admin) of the caller."""
    ident = get_authenticated_identity()
    role = str(getattr(ident, "platform_role", "") or session.get("role") or "").upper()
    return (getattr(ident, "user_id", None) or session.get("user_id")), role in ADMIN_ROLES


def _visible(query):
    user_id, is_admin = _who()
    if is_admin:
        return query
    if not user_id:  # never match unowned accounts for an unidentified caller
        return query.filter(db.false())
    return query.filter(CrmAccount.owner_user_id == user_id)


def _account_or_404(account_id: str):
    row = _visible(CrmAccount.query).filter(CrmAccount.id == account_id).first()
    if row is None:
        return None, ({"success": False, "error": "Không tìm thấy khách hàng."}, 404)
    return row, None


def _month_range(month: str | None) -> tuple[str, datetime, datetime]:
    today = datetime.utcnow()
    try:
        first = datetime.strptime(month or "", "%Y-%m")
    except ValueError:
        first = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    nxt = first.replace(year=first.year + (first.month == 12), month=first.month % 12 + 1)
    return first.strftime("%Y-%m"), first, nxt


def _actuals(org_ids: list[str], start: datetime, end: datetime, with_margin: bool) -> dict[str, dict]:
    """Per organization: cases, revenue (and margin) in [start, end), plus its last order time ever."""
    out: dict[str, dict] = {}
    if not org_ids:
        return out
    rows = (
        BizOrder.query.filter(BizOrder.organization_id.in_(org_ids), BizOrder.status != "cancelled", BizOrder.created_at >= start, BizOrder.created_at < end).all()
    )
    costs = {}
    if with_margin and rows:
        for c in OrderLabCost.query.filter(OrderLabCost.order_code.in_([o.order_code for o in rows])).all():
            costs[c.order_code] = c
    for o in rows:
        d = out.setdefault(o.organization_id, {"cases": 0, "revenue": 0.0, "margin": 0.0})
        d["cases"] += 1
        d["revenue"] += o.total_amount or 0
        c = costs.get(o.order_code)
        if c is not None and c.missing_count == 0:
            d["margin"] += c.sell_total - c.cost_total
    return out


def _last_orders(org_ids: list[str]) -> dict[str, datetime]:
    if not org_ids:
        return {}
    rows = (
        db.session.query(BizOrder.organization_id, db.func.max(BizOrder.created_at))
        .filter(BizOrder.organization_id.in_(org_ids), BizOrder.status != "cancelled")
        .group_by(BizOrder.organization_id)
        .all()
    )
    return {r[0]: r[1] for r in rows}


def _row(a: CrmAccount, act: dict, last_order: datetime | None, with_margin: bool) -> dict:
    cases = act.get("cases", 0)
    est = a.est_monthly_cases or 0
    today = datetime.utcnow().date().isoformat()
    row = {
        "id": a.id,
        "name": a.name,
        "account_type": a.account_type,
        "organization_id": a.organization_id,
        "stage": a.stage,
        "owner_user_id": a.owner_user_id,
        "owner_name": a.owner_name,
        "contact_person": a.contact_person,
        "phone": a.phone,
        "address": a.address,
        "district": a.district,
        "est_monthly_cases": est,
        "next_followup_date": a.next_followup_date,
        "followup_overdue": bool(a.next_followup_date and a.next_followup_date < today),
        "notes": a.notes,
        "cases": cases,
        "revenue": round(act.get("revenue", 0.0), 2),
        "share_pct": round(cases / est * 100, 1) if est else None,
        "days_quiet": (datetime.utcnow() - last_order).days if last_order else None,
        "last_activity_at": a.last_activity_at.isoformat() if a.last_activity_at else None,
    }
    if with_margin:
        row["margin"] = round(act.get("margin", 0.0), 2)
    return row


@crm_sales_bp.route("/accounts", methods=["GET"])
@crm_access
def accounts_list():
    _, is_admin = _who()
    month, start, end = _month_range(request.args.get("month"))
    query = _visible(CrmAccount.query)
    stage = _clean(request.args.get("stage"), 20).upper()
    if stage in STAGES:
        query = query.filter(CrmAccount.stage == stage)
    term = _clean(request.args.get("q"), 60)
    if term:
        query = query.filter(CrmAccount.name.ilike(f"%{term}%"))
    owner = _clean(request.args.get("owner"), 36)
    if owner and is_admin:
        query = query.filter(CrmAccount.owner_user_id == owner)
    accounts = query.order_by(CrmAccount.name).limit(500).all()
    org_ids = [a.organization_id for a in accounts if a.organization_id]
    acts = _actuals(org_ids, start, end, is_admin)
    lasts = _last_orders(org_ids)
    rows = [_row(a, acts.get(a.organization_id, {}), lasts.get(a.organization_id), is_admin) for a in accounts]
    counts = {s: 0 for s in STAGES}
    for a in _visible(CrmAccount.query).all():
        counts[a.stage] = counts.get(a.stage, 0) + 1
    est = sum(r["est_monthly_cases"] for r in rows if r["organization_id"])
    cases = sum(r["cases"] for r in rows if r["organization_id"])
    totals = {
        "accounts": len(rows),
        "est_monthly_cases": est,
        "cases": cases,
        "share_pct": round(cases / est * 100, 1) if est else None,
        "revenue": round(sum(r["revenue"] for r in rows), 2),
        "overdue_followups": sum(1 for r in rows if r["followup_overdue"]),
        "quiet_accounts": sum(1 for r in rows if r["stage"] == "ACTIVE" and (r["days_quiet"] is None or r["days_quiet"] > 30)),
    }
    if is_admin:
        totals["margin"] = round(sum(r.get("margin", 0) for r in rows), 2)
    return {"success": True, "data": {"month": month, "is_admin": is_admin, "stage_counts": counts, "totals": totals, "accounts": rows}}, 200


def _apply_fields(row: CrmAccount, body: dict, is_admin: bool) -> str | None:
    if "name" in body:
        name = _clean(body.get("name"), 200)
        if not name:
            return "Cần nhập tên khách hàng."
        row.name = name
    if "account_type" in body:
        t = _clean(body.get("account_type"), 20).upper()
        if t not in ACCOUNT_TYPES:
            return "Loại khách hàng không hợp lệ."
        row.account_type = t
    if "stage" in body:
        s = _clean(body.get("stage"), 20).upper()
        if s not in STAGES:
            return "Giai đoạn không hợp lệ."
        row.stage = s
    for key, limit in (("contact_person", 120), ("phone", 40), ("address", 300), ("district", 80), ("notes", 1000)):
        if key in body:
            setattr(row, key, _clean(body.get(key), limit) or None)
    if "est_monthly_cases" in body:
        try:
            n = int(body.get("est_monthly_cases") or 0)
        except (TypeError, ValueError):
            return "Số ca ước tính không hợp lệ."
        if n < 0 or n > 1_000_000:
            return "Số ca ước tính không hợp lệ."
        row.est_monthly_cases = n
    if "next_followup_date" in body:
        raw = _clean(body.get("next_followup_date"), 10)
        if raw:
            d = parse_date(raw)
            if d is None:
                return "Ngày hẹn chăm sóc không hợp lệ (YYYY-MM-DD)."
            row.next_followup_date = d.isoformat()
        else:
            row.next_followup_date = None
    if is_admin and "owner_user_id" in body:
        owner_id = _clean(body.get("owner_user_id"), 36)
        if owner_id:
            user = db.session.get(User, owner_id)
            if user is None or str(user.role).upper() != "SALE":
                return "Người phụ trách phải là tài khoản vai trò Sale."
            row.owner_user_id, row.owner_name = user.id, user.email
        else:
            row.owner_user_id = row.owner_name = None
    if is_admin and "organization_id" in body:
        org_id = _clean(body.get("organization_id"), 36)
        if org_id:
            if db.session.get(PartnerOrganization, org_id) is None:
                return "Không tìm thấy đơn vị để liên kết."
            taken = CrmAccount.query.filter(CrmAccount.organization_id == org_id, CrmAccount.id != row.id).first()
            if taken is not None:
                return f"Đơn vị này đã gắn với khách hàng “{taken.name}”."
            row.organization_id = org_id
        else:
            row.organization_id = None
    return None


@crm_sales_bp.route("/accounts", methods=["POST"])
@crm_access
def account_create():
    user_id, is_admin = _who()
    body = request.get_json(silent=True) or {}
    row = CrmAccount(name="", created_by=(_actor() or "")[:120] or None)
    if not is_admin:  # a sale always owns what they create
        user = db.session.get(User, user_id)
        row.owner_user_id, row.owner_name = user_id, getattr(user, "email", None)
    err = _apply_fields(row, body, is_admin)
    if err:
        return {"success": False, "error": err}, 400
    if not row.name:
        return {"success": False, "error": "Cần nhập tên khách hàng."}, 400
    db.session.add(row)
    write_audit("CRM_ACCOUNT_CREATED", "CrmAccount", row.name[:50], user_email=_actor() or "SYSTEM", ip_address=_client_ip())
    db.session.commit()
    return {"success": True, "data": {"id": row.id}}, 201


@crm_sales_bp.route("/accounts/<account_id>", methods=["POST"])
@crm_access
def account_update(account_id: str):
    row, err = _account_or_404(account_id)
    if err is not None:
        return err
    _, is_admin = _who()
    msg = _apply_fields(row, request.get_json(silent=True) or {}, is_admin)
    if msg:
        return {"success": False, "error": msg}, 400
    db.session.commit()
    return {"success": True}, 200


@crm_sales_bp.route("/accounts/<account_id>", methods=["GET"])
@crm_access
def account_detail(account_id: str):
    row, err = _account_or_404(account_id)
    if err is not None:
        return err
    _, is_admin = _who()
    activities = CrmActivity.query.filter_by(account_id=row.id).order_by(CrmActivity.created_at.desc()).limit(100).all()
    history = []
    if row.organization_id:
        now = datetime.utcnow()
        y, m = now.year, now.month
        for _ in range(6):
            month, start, end = _month_range(f"{y:04d}-{m:02d}")
            a = _actuals([row.organization_id], start, end, is_admin).get(row.organization_id, {})
            history.append({"month": month, "cases": a.get("cases", 0), "revenue": round(a.get("revenue", 0.0), 2)})
            m -= 1
            if m == 0:
                y, m = y - 1, 12
        history.reverse()
    return {
        "success": True,
        "data": {
            "account": {
                **_row(row, {}, None, False),
                "organization_id": row.organization_id,
            },
            "history": history,
            "activities": [
                {"id": a.id, "kind": a.kind, "summary": a.summary, "by": a.created_by_name, "at": a.created_at.isoformat() if a.created_at else None}
                for a in activities
            ],
        },
    }, 200


@crm_sales_bp.route("/accounts/<account_id>/activities", methods=["POST"])
@crm_access
def activity_add(account_id: str):
    row, err = _account_or_404(account_id)
    if err is not None:
        return err
    body = request.get_json(silent=True) or {}
    kind = _clean(body.get("kind"), 20).upper() or "NOTE"
    summary = _clean(body.get("summary"), 1000)
    if kind not in ACTIVITY_KINDS or not summary:
        return {"success": False, "error": "Cần chọn loại liên hệ và nhập nội dung."}, 400
    user_id, _ = _who()
    user = db.session.get(User, user_id) if user_id else None
    db.session.add(CrmActivity(account_id=row.id, kind=kind, summary=summary, created_by_user_id=user_id, created_by_name=getattr(user, "email", None)))
    row.last_activity_at = datetime.utcnow()
    if "next_followup_date" in body:
        raw = _clean(body.get("next_followup_date"), 10)
        d = parse_date(raw) if raw else None
        if raw and d is None:
            return {"success": False, "error": "Ngày hẹn chăm sóc không hợp lệ (YYYY-MM-DD)."}, 400
        row.next_followup_date = d.isoformat() if d else None
    db.session.commit()
    return {"success": True}, 201


# ------------------------------------------------------------------ sales staff (admin)


@crm_sales_bp.route("/sales", methods=["GET"])
@admin_only
def sales_list():
    month, start, end = _month_range(request.args.get("month"))
    users = User.query.filter(User.role == "SALE").order_by(User.email).all()
    accounts = CrmAccount.query.all()
    acts = _actuals([a.organization_id for a in accounts if a.organization_id], start, end, True)
    targets = {t.user_id: t for t in CrmSaleTarget.query.filter_by(month=month)}
    out = []
    for u in users:
        mine = [a for a in accounts if a.owner_user_id == u.id]
        cases = revenue = margin = 0.0
        for a in mine:
            d = acts.get(a.organization_id, {}) if a.organization_id else {}
            cases += d.get("cases", 0)
            revenue += d.get("revenue", 0.0)
            margin += d.get("margin", 0.0)
        t = targets.get(u.id)
        tc, tr = (t.target_cases, t.target_revenue) if t else (0, 0.0)
        out.append(
            {
                "user_id": u.id,
                "email": u.email,
                "accounts": len(mine),
                "active_accounts": sum(1 for a in mine if a.stage == "ACTIVE"),
                "cases": int(cases),
                "revenue": round(revenue, 2),
                "margin": round(margin, 2),
                "target_cases": tc,
                "target_revenue": tr,
                "cases_pct": round(cases / tc * 100, 1) if tc else None,
                "revenue_pct": round(revenue / tr * 100, 1) if tr else None,
            }
        )
    return {"success": True, "data": {"month": month, "sales": out}}, 200


@crm_sales_bp.route("/sales/<user_id>/target", methods=["POST"])
@admin_only
def sale_target_set(user_id: str):
    user = db.session.get(User, user_id)
    if user is None or str(user.role).upper() != "SALE":
        return {"success": False, "error": "Không tìm thấy tài khoản Sale."}, 404
    body = request.get_json(silent=True) or {}
    month, _s, _e = _month_range(_clean(body.get("month"), 7))
    try:
        cases = int(body.get("target_cases") or 0)
        revenue = float(body.get("target_revenue") or 0)
    except (TypeError, ValueError):
        return {"success": False, "error": "Chỉ tiêu không hợp lệ."}, 400
    if cases < 0 or revenue < 0:
        return {"success": False, "error": "Chỉ tiêu không được âm."}, 400
    row = CrmSaleTarget.query.filter_by(user_id=user_id, month=month).first()
    if row is None:
        row = CrmSaleTarget(user_id=user_id, month=month)
        db.session.add(row)
    row.target_cases, row.target_revenue = cases, revenue
    row.updated_by = (_actor() or "")[:120] or None
    write_audit("CRM_SALE_TARGET_SET", "User", user.email[:50], user_email=_actor() or "SYSTEM", ip_address=_client_ip())
    db.session.commit()
    return {"success": True}, 200


# ------------------------------------------------------------- Excel export / import

TYPE_VI = {"CLINIC": "Phòng khám", "HOSPITAL": "Bệnh viện", "OTHER": "Khác"}
STAGE_VI = {
    "LEAD": "Tiềm năng",
    "MET": "Đã gặp",
    "QUOTED": "Đã báo giá",
    "CONTRACTED": "Đã ký hợp đồng",
    "ACTIVE": "Đang gửi mẫu",
    "LOST": "Ngừng / mất",
}
MAX_IMPORT_ROWS = 1000
IMPORT_HEADER = [
    "Tên khách hàng (bắt buộc)",
    "Loại (Phòng khám / Bệnh viện / Khác)",
    "Người liên hệ",
    "Điện thoại",
    "Địa chỉ",
    "Quận / khu vực",
    "Ước tính ca / tháng",
    "Giai đoạn",
    "Ngày hẹn chăm sóc (YYYY-MM-DD)",
    "Ghi chú",
    "Sale phụ trách (email, chỉ Admin)",
]
_IMPORT_FIELDS = ["name", "account_type", "contact_person", "phone", "address", "district", "est_monthly_cases", "stage", "next_followup_date", "notes", "owner_email"]


def _fold(text: str) -> str:
    import unicodedata

    t = unicodedata.normalize("NFKD", str(text or "")).replace("đ", "d").replace("Đ", "D")
    return " ".join("".join(c for c in t if not unicodedata.combining(c)).lower().split())


_TYPE_LOOKUP = {_fold(v): k for k, v in TYPE_VI.items()} | {k.lower(): k for k in TYPE_VI}
_STAGE_LOOKUP = {_fold(v): k for k, v in STAGE_VI.items()} | {k.lower(): k for k in STAGE_VI}


@crm_sales_bp.route("/accounts/export", methods=["GET"])
@crm_access
def accounts_export():
    _, is_admin = _who()
    month, start, end = _month_range(request.args.get("month"))
    accounts = _visible(CrmAccount.query).order_by(CrmAccount.name).limit(5000).all()
    org_ids = [a.organization_id for a in accounts if a.organization_id]
    acts = _actuals(org_ids, start, end, is_admin)
    lasts = _last_orders(org_ids)
    head = ["Tên khách hàng", "Loại", "Giai đoạn", "Sale phụ trách", "Người liên hệ", "Điện thoại", "Địa chỉ", "Quận / khu vực",
            "Ước tính ca / tháng", f"Số ca thực nhận {month}", "Thị phần %", f"Doanh thu {month}"]
    if is_admin:
        head.append(f"Lãi {month}")
    head += ["Ngày hẹn chăm sóc", "Ngày chưa có đơn", "Ghi chú"]
    rows = []
    for a in accounts:
        r = _row(a, acts.get(a.organization_id, {}), lasts.get(a.organization_id), is_admin)
        line = [r["name"], TYPE_VI.get(r["account_type"], r["account_type"]), STAGE_VI.get(r["stage"], r["stage"]), r["owner_name"] or "",
                r["contact_person"] or "", r["phone"] or "", r["address"] or "", r["district"] or "", r["est_monthly_cases"],
                r["cases"], r["share_pct"] if r["share_pct"] is not None else "", r["revenue"]]
        if is_admin:
            line.append(r.get("margin", 0))
        line += [r["next_followup_date"] or "", r["days_quiet"] if r["days_quiet"] is not None else "", r["notes"] or ""]
        rows.append(line)
    money = {11, 12} if is_admin else {11}
    return xlsx_response(build_xlsx([("Khách hàng", head, rows)], {"Khách hàng": money}), f"khach-hang-{month}")


@crm_sales_bp.route("/accounts/import/template", methods=["GET"])
@crm_access
def accounts_import_template():
    example = ["Phòng khám Ví dụ", "Phòng khám", "BS. Nguyễn Văn A", "0901234567", "12 Đường ABC", "Quận 1", 120, "Tiềm năng", "", "Gặp lần đầu qua giới thiệu", ""]
    return xlsx_response(build_xlsx([("Khách hàng", IMPORT_HEADER, [example])]), "mau-nhap-khach-hang")


def _read_import_rows(filename: str, data: bytes) -> list[list[str]]:
    import csv
    import io

    from app.clinic_billing.bulk import _cell_text

    name = (filename or "").lower()
    if name.endswith((".xlsx", ".xlsm")):
        from openpyxl import load_workbook

        wb = load_workbook(io.BytesIO(data), read_only=True, data_only=True)
        return [[_cell_text(c) for c in r] for r in wb.worksheets[0].iter_rows(values_only=True)]
    text = data.decode("utf-8-sig", errors="replace")
    delim = "\t" if "\t" in text.splitlines()[0] else (";" if text.splitlines()[0].count(";") > text.splitlines()[0].count(",") else ",")
    return [[c.strip() for c in row] for row in csv.reader(io.StringIO(text), delimiter=delim)]


@crm_sales_bp.route("/accounts/import", methods=["POST"])
@crm_access
def accounts_import():
    """Bulk-add customers from an Excel/CSV form. apply=0 only checks; apply=1 saves valid rows. Duplicates (same name) are skipped."""
    user_id, is_admin = _who()
    f = request.files.get("file")
    if f is None or not f.filename:
        return {"success": False, "error": "Chưa chọn file."}, 400
    data = f.read(MAX_UPLOAD_BYTES + 1)
    if len(data) > MAX_UPLOAD_BYTES:
        return {"success": False, "error": "File quá lớn (tối đa 2MB)."}, 413
    try:
        grid = _read_import_rows(f.filename, data)
    except Exception:
        return {"success": False, "error": "Không đọc được file. Hãy dùng file Excel (.xlsx) hoặc CSV theo biểu mẫu."}, 400
    body_rows = [(i + 2, r) for i, r in enumerate(grid[1:]) if any(str(c).strip() for c in r)]
    if not body_rows:
        return {"success": False, "error": "File không có dòng dữ liệu nào."}, 400
    if len(body_rows) > MAX_IMPORT_ROWS:
        return {"success": False, "error": f"Tối đa {MAX_IMPORT_ROWS} dòng mỗi lần nhập."}, 400
    apply = request.form.get("apply") == "1"

    existing = {_fold(n) for (n,) in db.session.query(CrmAccount.name).all()}
    sale_by_email = {}
    if is_admin:
        sale_by_email = {str(u.email).lower(): u for u in User.query.filter(User.role == "SALE").all()}
    owner = db.session.get(User, user_id) if not is_admin else None
    created, errors, skipped = 0, [], []
    seen: set[str] = set()
    for line_no, cells in body_rows:
        cells = list(cells) + [""] * (len(_IMPORT_FIELDS) - len(cells))
        raw = dict(zip(_IMPORT_FIELDS, cells))
        key = _fold(_clean(raw["name"], 200))
        if not key:
            errors.append({"row": line_no, "error": "Thiếu tên khách hàng."})
            continue
        if key in existing or key in seen:
            skipped.append({"row": line_no, "name": raw["name"], "reason": "Đã có khách hàng trùng tên."})
            continue
        body = {k: raw[k] for k in ("name", "contact_person", "phone", "address", "district", "notes", "next_followup_date")}
        body["est_monthly_cases"] = raw["est_monthly_cases"] or 0
        body["next_followup_date"] = str(raw["next_followup_date"])[:10]  # Excel date cells arrive as "YYYY-MM-DD 00:00:00"
        t = _fold(raw["account_type"]) or "phong kham"
        body["account_type"] = _TYPE_LOOKUP.get(t, "")
        s_ = _fold(raw["stage"]) or "tiem nang"
        body["stage"] = _STAGE_LOOKUP.get(s_, "")
        row = CrmAccount(name="", created_by=(_actor() or "")[:120] or None)
        if not is_admin:
            row.owner_user_id, row.owner_name = user_id, getattr(owner, "email", None)
        else:
            email = _clean(raw["owner_email"], 120).lower()
            if email:
                sale = sale_by_email.get(email)
                if sale is None:
                    errors.append({"row": line_no, "error": f"Không có tài khoản Sale “{email}”."})
                    continue
                body["owner_user_id"] = sale.id
        if not body["account_type"]:
            errors.append({"row": line_no, "error": "Loại khách hàng không hợp lệ (Phòng khám / Bệnh viện / Khác)."})
            continue
        if not body["stage"]:
            errors.append({"row": line_no, "error": "Giai đoạn không hợp lệ."})
            continue
        err = _apply_fields(row, body, is_admin)
        if err:
            errors.append({"row": line_no, "error": err})
            continue
        seen.add(key)
        created += 1
        if apply:
            db.session.add(row)
    if apply and created:
        write_audit("CRM_ACCOUNTS_IMPORTED", "CrmAccount", str(created), user_email=_actor() or "SYSTEM", ip_address=_client_ip())
        db.session.commit()
    elif apply:
        db.session.rollback()
    return {"success": True, "data": {"applied": apply, "created": created, "skipped": skipped[:50], "skipped_count": len(skipped), "errors": errors[:50], "error_count": len(errors)}}, 200
