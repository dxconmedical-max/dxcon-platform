"""Per-clinic contracts, price lists, statements (kết toán) and receivables (công nợ). DxCon admin staff only."""

from __future__ import annotations

from datetime import datetime

from flask import Blueprint, Response, current_app, request
from sqlalchemy import func

from app.api.reception_workspace.routes import _actor, _client_ip, _dxcon_staff_error
from app.clinic_billing.logic import (
    aging_summary,
    allocate_payments,
    due_date_for,
    parse_date,
    parse_price_lines,
)
from app.core.audit import write_audit
from app.executive_platform.auth import executive_api_read, executive_api_write
from app.extensions.db import db
from app.models.biz_order import BizOrder
from app.models.clinic_billing import (
    ClinicBillingSetting,
    ClinicContract,
    ClinicPayment,
    ClinicPrice,
    ClinicStatement,
    ClinicStatementLine,
)
from app.models.partner_foundation import PartnerOrganization
from app.models.test_catalog import TestCatalog

clinic_billing_bp = Blueprint("clinic_billing", __name__, url_prefix="/api/v1/reception/workspace/clinic-billing")

CONTRACT_MAX_BYTES = 10 * 1024 * 1024


def _clean(value, limit: int) -> str:
    return " ".join(str(value or "").split())[:limit]


def _clinic_or_error(org_id: str):
    denied = _dxcon_staff_error()
    if denied is not None:
        return None, denied
    clinic = PartnerOrganization.query.filter_by(id=org_id, organization_type="CLINIC").first()
    if clinic is None:
        return None, ({"success": False, "error": "Không tìm thấy phòng khám."}, 404)
    return clinic, None


def _money(value) -> float:
    return round(float(value or 0), 2)


def _statements_allocated(org_id: str) -> tuple[list[dict], float]:
    rows = ClinicStatement.query.filter_by(organization_id=org_id).all()
    paid = sum(p.amount for p in ClinicPayment.query.filter_by(organization_id=org_id))
    plain = [
        {
            "id": s.id,
            "statement_no": s.statement_no,
            "period_start": s.period_start,
            "period_end": s.period_end,
            "order_count": s.order_count,
            "total_amount": s.total_amount,
            "due_date": s.due_date,
            "note": s.note,
            "created_at": s.created_at.isoformat() if s.created_at else None,
        }
        for s in rows
    ]
    return allocate_payments(plain, paid), _money(paid)


def _billed_order_codes() -> set[str]:
    return {c for (c,) in db.session.query(ClinicStatementLine.order_code).all()}


def _unbilled_orders(org_id: str, start: str | None = None, end: str | None = None):
    q = BizOrder.query.filter(BizOrder.organization_id == org_id, BizOrder.status != "cancelled")
    if start:
        q = q.filter(BizOrder.created_at >= datetime.fromisoformat(start))
    if end:
        q = q.filter(BizOrder.created_at < datetime.fromisoformat(end).replace(hour=23, minute=59, second=59))
    billed = _billed_order_codes()
    return [o for o in q.order_by(BizOrder.created_at).all() if o.order_code not in billed]


def _summary(org_id: str) -> dict:
    allocated, paid = _statements_allocated(org_id)
    billed = _money(sum(s["total_amount"] for s in allocated))
    outstanding = _money(sum(s["outstanding"] for s in allocated))
    unbilled = _unbilled_orders(org_id)
    return {
        "billed": billed,
        "paid": paid,
        "outstanding": outstanding,
        "credit": _money(max(paid - billed, 0)),
        "unbilled_orders": len(unbilled),
        "unbilled_amount": _money(sum(o.total_amount for o in unbilled)),
        "aging": aging_summary(allocated, datetime.utcnow().date()),
    }


# ------------------------------------------------------------- overview


@clinic_billing_bp.route("/receivables", methods=["GET"])
@executive_api_read
def receivables_overview():
    denied = _dxcon_staff_error()
    if denied is not None:
        return denied
    clinics = PartnerOrganization.query.filter_by(organization_type="CLINIC").order_by(PartnerOrganization.organization_name).all()
    data = []
    for c in clinics:
        s = _summary(c.id)
        active = bool(s["billed"] or s["paid"] or s["unbilled_orders"])
        data.append({"organization_id": c.id, "organization_name": c.organization_name, "has_activity": active, **s})
    # Every clinic is listed (a new clinic needs its contract and prices before its first order).
    data.sort(key=lambda r: (-r["outstanding"], -r["unbilled_amount"], r["organization_name"] or ""))
    return {
        "success": True,
        "data": {
            "clinics": data,
            "total_outstanding": _money(sum(r["outstanding"] for r in data)),
            "total_unbilled": _money(sum(r["unbilled_amount"] for r in data)),
        },
    }, 200


@clinic_billing_bp.route("/<org_id>", methods=["GET"])
@executive_api_read
def billing_overview(org_id: str):
    clinic, err = _clinic_or_error(org_id)
    if err is not None:
        return err
    setting = db.session.get(ClinicBillingSetting, org_id)
    allocated, _paid = _statements_allocated(org_id)
    allocated.sort(key=lambda s: s["period_start"], reverse=True)
    contracts = ClinicContract.query.filter_by(organization_id=org_id).order_by(ClinicContract.created_at.desc()).all()
    payments = ClinicPayment.query.filter_by(organization_id=org_id).order_by(ClinicPayment.paid_at.desc()).limit(50).all()
    return {
        "success": True,
        "data": {
            "clinic": {"id": clinic.id, "name": clinic.organization_name, "code": clinic.organization_code},
            "settings": {
                "default_discount_pct": setting.default_discount_pct if setting else 0,
                "payment_terms_days": setting.payment_terms_days if setting else 30,
            },
            "price_count": ClinicPrice.query.filter_by(organization_id=org_id).count(),
            "summary": _summary(org_id),
            "contracts": [
                {
                    "id": c.id,
                    "contract_no": c.contract_no,
                    "title": c.title,
                    "signed_date": c.signed_date,
                    "start_date": c.start_date,
                    "end_date": c.end_date,
                    "note": c.note,
                    "file_name": c.file_name,
                    "has_file": bool(c.file_id),
                }
                for c in contracts
            ],
            "statements": allocated,
            "payments": [
                {
                    "id": p.id,
                    "amount": p.amount,
                    "paid_at": p.paid_at,
                    "method": p.method,
                    "reference": p.reference,
                    "note": p.note,
                }
                for p in payments
            ],
        },
    }, 200


# ------------------------------------------------------------- settings & prices


@clinic_billing_bp.route("/<org_id>/settings", methods=["POST"])
@executive_api_write
def save_settings(org_id: str):
    clinic, err = _clinic_or_error(org_id)
    if err is not None:
        return err
    body = request.get_json(silent=True) or {}
    try:
        pct = float(body.get("default_discount_pct") or 0)
        terms = int(body.get("payment_terms_days") if body.get("payment_terms_days") not in (None, "") else 30)
    except (TypeError, ValueError):
        return {"success": False, "error": "Giá trị không hợp lệ."}, 400
    if not 0 <= pct <= 100 or not 0 <= terms <= 365:
        return {"success": False, "error": "Chiết khấu từ 0 đến 100%, hạn thanh toán từ 0 đến 365 ngày."}, 400
    row = db.session.get(ClinicBillingSetting, org_id) or ClinicBillingSetting(organization_id=org_id)
    row.default_discount_pct = pct
    row.payment_terms_days = terms
    row.updated_by = (_actor() or "")[:120] or None
    db.session.add(row)
    write_audit("CLINIC_BILLING_SETTINGS", "PartnerOrganization", clinic.organization_code, user_email=_actor() or "SYSTEM", ip_address=_client_ip())
    db.session.commit()
    return {"success": True}, 200


@clinic_billing_bp.route("/<org_id>/prices", methods=["GET"])
@executive_api_read
def list_prices(org_id: str):
    clinic, err = _clinic_or_error(org_id)
    if err is not None:
        return err
    term = _clean(request.args.get("q"), 60)
    only_custom = request.args.get("custom") == "1"
    query = TestCatalog.query
    if term:
        like = f"%{term}%"
        query = query.filter(TestCatalog.code.ilike(like) | TestCatalog.name.ilike(like))
    prices = {p.test_catalog_id: p.price for p in ClinicPrice.query.filter_by(organization_id=org_id)}
    if only_custom:
        query = query.filter(TestCatalog.id.in_(list(prices) or [""]))
    rows = query.order_by(TestCatalog.name).limit(40).all()
    return {
        "success": True,
        "data": [
            {"id": t.id, "code": t.code, "name": t.name, "list_price": t.price or 0, "clinic_price": prices.get(t.id)}
            for t in rows
        ],
    }, 200


@clinic_billing_bp.route("/<org_id>/prices/<test_id>", methods=["POST"])
@executive_api_write
def set_price(org_id: str, test_id: str):
    clinic, err = _clinic_or_error(org_id)
    if err is not None:
        return err
    if db.session.get(TestCatalog, test_id) is None:
        return {"success": False, "error": "Không tìm thấy xét nghiệm."}, 404
    body = request.get_json(silent=True) or {}
    row = ClinicPrice.query.filter_by(organization_id=org_id, test_catalog_id=test_id).first()
    raw = body.get("price")
    if raw in (None, ""):  # clearing the price falls back to the catalog price
        if row is not None:
            db.session.delete(row)
            db.session.commit()
        return {"success": True}, 200
    try:
        price = float(raw)
    except (TypeError, ValueError):
        return {"success": False, "error": "Giá không hợp lệ."}, 400
    if price < 0 or price > 1_000_000_000:
        return {"success": False, "error": "Giá phải từ 0 trở lên."}, 400
    if row is None:
        row = ClinicPrice(organization_id=org_id, test_catalog_id=test_id, price=price)
        db.session.add(row)
    row.price = price
    row.updated_by = (_actor() or "")[:120] or None
    write_audit("CLINIC_PRICE_SET", "PartnerOrganization", clinic.organization_code, user_email=_actor() or "SYSTEM", ip_address=_client_ip())
    db.session.commit()
    return {"success": True}, 200


@clinic_billing_bp.route("/<org_id>/prices/bulk", methods=["POST"])
@executive_api_write
def set_prices_bulk(org_id: str):
    """Paste many 'code price' lines at once. apply=false only checks (dry run)."""
    clinic, err = _clinic_or_error(org_id)
    if err is not None:
        return err
    body = request.get_json(silent=True) or {}
    rows = parse_price_lines(str(body.get("text") or ""))
    if not rows:
        return {"success": False, "error": "Chưa có dòng nào. Mỗi dòng gồm mã xét nghiệm và giá."}, 400
    codes = {r["code"].upper() for r in rows if not r["error"]}
    tests = {}
    if codes:
        for t in TestCatalog.query.filter(func.upper(TestCatalog.code).in_(list(codes))).all():
            tests.setdefault(t.code.upper(), t)
    existing = {p.test_catalog_id: p for p in ClinicPrice.query.filter_by(organization_id=org_id)}
    apply = body.get("apply") is True
    actor = (_actor() or "")[:120] or None
    created = updated = removed = 0
    errors = []
    for r in rows:
        if r["error"]:
            errors.append({"line": r["line"], "code": r["code"], "error": r["error"]})
            continue
        test = tests.get(r["code"].upper())
        if test is None:
            errors.append({"line": r["line"], "code": r["code"], "error": "Không có mã này trong danh mục xét nghiệm."})
            continue
        row = existing.get(test.id)
        if r["remove"]:
            if row is not None:
                removed += 1
                if apply:
                    db.session.delete(row)
                    existing.pop(test.id, None)
            continue
        if row is None:
            created += 1
            if apply:
                row = ClinicPrice(organization_id=org_id, test_catalog_id=test.id, price=r["price"], updated_by=actor)
                db.session.add(row)
                existing[test.id] = row
        else:
            updated += 1
            if apply:
                row.price = r["price"]
                row.updated_by = actor
    if apply and (created or updated or removed):
        write_audit("CLINIC_PRICE_BULK", "PartnerOrganization", clinic.organization_code, user_email=_actor() or "SYSTEM", ip_address=_client_ip())
        db.session.commit()
    return {
        "success": True,
        "data": {"applied": apply, "created": created, "updated": updated, "removed": removed, "errors": errors},
    }, 200


# ------------------------------------------------------------- contracts


@clinic_billing_bp.route("/<org_id>/contracts", methods=["POST"])
@executive_api_write
def add_contract(org_id: str):
    clinic, err = _clinic_or_error(org_id)
    if err is not None:
        return err
    form = request.form
    title = _clean(form.get("title"), 200)
    if len(title) < 3:
        return {"success": False, "error": "Vui lòng nhập tên hợp đồng."}, 400
    dates = {}
    for key in ("signed_date", "start_date", "end_date"):
        raw = _clean(form.get(key), 10)
        if raw and parse_date(raw) is None:
            return {"success": False, "error": "Ngày không hợp lệ (YYYY-MM-DD)."}, 400
        dates[key] = raw or None
    file_id = file_name = None
    upload = request.files.get("file")
    if upload is not None and upload.filename:
        data = upload.read()
        if len(data) > CONTRACT_MAX_BYTES:
            return {"success": False, "error": "File tối đa 10MB."}, 400
        from app.storage.attachment_service import AttachmentService

        try:
            meta = AttachmentService.upload_file(
                filename=upload.filename,
                content_type=upload.mimetype or "application/octet-stream",
                data=data,
                tenant_id=org_id,
            )
        except ValueError as exc:
            return {"success": False, "error": f"Không tải được file ({exc}). Chỉ nhận PDF hoặc ảnh JPG/PNG."}, 400
        file_id, file_name = meta["id"], meta["filename"]
    row = ClinicContract(
        organization_id=org_id,
        contract_no=_clean(form.get("contract_no"), 80) or None,
        title=title,
        note=_clean(form.get("note"), 500) or None,
        file_id=file_id,
        file_name=file_name,
        created_by=(_actor() or "")[:120] or None,
        **dates,
    )
    db.session.add(row)
    write_audit("CLINIC_CONTRACT_ADDED", "PartnerOrganization", clinic.organization_code, user_email=_actor() or "SYSTEM", ip_address=_client_ip())
    db.session.commit()
    return {"success": True, "data": {"id": row.id}}, 201


@clinic_billing_bp.route("/<org_id>/contracts/<contract_id>/file", methods=["GET"])
@executive_api_read
def contract_file(org_id: str, contract_id: str):
    clinic, err = _clinic_or_error(org_id)
    if err is not None:
        return err
    row = ClinicContract.query.filter_by(id=contract_id, organization_id=org_id).first()
    if row is None or not row.file_id:
        return {"success": False, "error": "Hợp đồng chưa có file đính kèm."}, 404
    from app.storage.factory import get_storage_provider
    from app.storage.models import FileMetadata

    meta = db.session.get(FileMetadata, row.file_id)
    if meta is None:
        return {"success": False, "error": "Không tìm thấy file."}, 404
    data = get_storage_provider(current_app._get_current_object()).get(meta.storage_key)
    write_audit("CLINIC_CONTRACT_DOWNLOADED", "PartnerOrganization", clinic.organization_code, user_email=_actor() or "SYSTEM", ip_address=_client_ip())
    db.session.commit()
    return Response(
        data,
        mimetype=meta.content_type,
        headers={"Content-Disposition": f'attachment; filename="{meta.filename}"'},
    )


# ------------------------------------------------------------- statements & payments


def _period(body: dict):
    start, end = _clean(body.get("period_start"), 10), _clean(body.get("period_end"), 10)
    ds, de = parse_date(start), parse_date(end)
    if ds is None or de is None or de < ds:
        return None, None, "Kỳ kết toán không hợp lệ (từ ngày – đến ngày, định dạng YYYY-MM-DD)."
    return ds, de, None


@clinic_billing_bp.route("/<org_id>/statements/preview", methods=["POST"])
@executive_api_write
def statement_preview(org_id: str):
    clinic, err = _clinic_or_error(org_id)
    if err is not None:
        return err
    ds, de, msg = _period(request.get_json(silent=True) or {})
    if msg:
        return {"success": False, "error": msg}, 400
    orders = _unbilled_orders(org_id, ds.isoformat(), de.isoformat())
    return {
        "success": True,
        "data": {"order_count": len(orders), "total_amount": _money(sum(o.total_amount for o in orders))},
    }, 200


@clinic_billing_bp.route("/<org_id>/statements", methods=["POST"])
@executive_api_write
def statement_create(org_id: str):
    clinic, err = _clinic_or_error(org_id)
    if err is not None:
        return err
    body = request.get_json(silent=True) or {}
    ds, de, msg = _period(body)
    if msg:
        return {"success": False, "error": msg}, 400
    orders = _unbilled_orders(org_id, ds.isoformat(), de.isoformat())
    if not orders:
        return {"success": False, "error": "Không có đơn nào chưa kết toán trong kỳ này."}, 409
    setting = db.session.get(ClinicBillingSetting, org_id)
    terms = setting.payment_terms_days if setting else 30
    count = ClinicStatement.query.filter_by(organization_id=org_id).count() + 1
    stmt_no = f"KT-{clinic.organization_code}-{de.strftime('%Y%m')}-{count:02d}"
    while ClinicStatement.query.filter_by(statement_no=stmt_no).first() is not None:
        count += 1
        stmt_no = f"KT-{clinic.organization_code}-{de.strftime('%Y%m')}-{count:02d}"
    stmt = ClinicStatement(
        organization_id=org_id,
        statement_no=stmt_no[:40],
        period_start=ds.isoformat(),
        period_end=de.isoformat(),
        order_count=len(orders),
        total_amount=_money(sum(o.total_amount for o in orders)),
        due_date=due_date_for(de, terms).isoformat(),
        note=_clean(body.get("note"), 300) or None,
        created_by=(_actor() or "")[:120] or None,
    )
    db.session.add(stmt)
    db.session.flush()
    for o in orders:
        db.session.add(
            ClinicStatementLine(
                statement_id=stmt.id,
                order_code=o.order_code,
                patient_name=o.patient_name,
                amount=_money(o.total_amount),
                ordered_at=o.created_at,
            )
        )
    write_audit("CLINIC_STATEMENT_CREATED", "ClinicStatement", stmt.statement_no, user_email=_actor() or "SYSTEM", ip_address=_client_ip())
    db.session.commit()
    return {"success": True, "data": {"id": stmt.id, "statement_no": stmt.statement_no, "total_amount": stmt.total_amount}}, 201


@clinic_billing_bp.route("/<org_id>/statements/<statement_id>", methods=["GET"])
@executive_api_read
def statement_detail(org_id: str, statement_id: str):
    clinic, err = _clinic_or_error(org_id)
    if err is not None:
        return err
    stmt = ClinicStatement.query.filter_by(id=statement_id, organization_id=org_id).first()
    if stmt is None:
        return {"success": False, "error": "Không tìm thấy bảng kết toán."}, 404
    lines = ClinicStatementLine.query.filter_by(statement_id=stmt.id).order_by(ClinicStatementLine.ordered_at).all()
    return {
        "success": True,
        "data": {
            "statement_no": stmt.statement_no,
            "clinic_name": clinic.organization_name,
            "period_start": stmt.period_start,
            "period_end": stmt.period_end,
            "due_date": stmt.due_date,
            "total_amount": stmt.total_amount,
            "lines": [
                {
                    "order_code": l.order_code,
                    "patient_name": l.patient_name,
                    "amount": l.amount,
                    "ordered_at": l.ordered_at.isoformat() if l.ordered_at else None,
                }
                for l in lines
            ],
        },
    }, 200


@clinic_billing_bp.route("/<org_id>/statements/<statement_id>/void", methods=["POST"])
@executive_api_write
def statement_void(org_id: str, statement_id: str):
    clinic, err = _clinic_or_error(org_id)
    if err is not None:
        return err
    stmt = ClinicStatement.query.filter_by(id=statement_id, organization_id=org_id).first()
    if stmt is None:
        return {"success": False, "error": "Không tìm thấy bảng kết toán."}, 404
    if ClinicPayment.query.filter_by(organization_id=org_id).count():
        return {
            "success": False,
            "error": "Phòng khám đã có khoản thanh toán nên không hủy được bảng kết toán. Hãy tạo kỳ kết toán mới để điều chỉnh.",
        }, 409
    ClinicStatementLine.query.filter_by(statement_id=stmt.id).delete()
    db.session.delete(stmt)
    write_audit("CLINIC_STATEMENT_VOIDED", "ClinicStatement", stmt.statement_no, user_email=_actor() or "SYSTEM", ip_address=_client_ip())
    db.session.commit()
    return {"success": True}, 200


@clinic_billing_bp.route("/<org_id>/payments", methods=["POST"])
@executive_api_write
def payment_add(org_id: str):
    clinic, err = _clinic_or_error(org_id)
    if err is not None:
        return err
    body = request.get_json(silent=True) or {}
    try:
        amount = float(body.get("amount"))
    except (TypeError, ValueError):
        return {"success": False, "error": "Số tiền không hợp lệ."}, 400
    if amount <= 0 or amount > 10_000_000_000:
        return {"success": False, "error": "Số tiền phải lớn hơn 0."}, 400
    paid_at = _clean(body.get("paid_at"), 10) or datetime.utcnow().date().isoformat()
    if parse_date(paid_at) is None:
        return {"success": False, "error": "Ngày thanh toán không hợp lệ."}, 400
    row = ClinicPayment(
        organization_id=org_id,
        amount=round(amount, 2),
        paid_at=paid_at,
        method=_clean(body.get("method"), 40) or None,
        reference=_clean(body.get("reference"), 120) or None,
        note=_clean(body.get("note"), 300) or None,
        created_by=(_actor() or "")[:120] or None,
    )
    db.session.add(row)
    write_audit("CLINIC_PAYMENT_ADDED", "PartnerOrganization", clinic.organization_code, user_email=_actor() or "SYSTEM", ip_address=_client_ip())
    db.session.commit()
    return {"success": True, "data": {"id": row.id}}, 201
