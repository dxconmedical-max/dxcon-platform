"""Import lab reference ranges from the DxCon spreadsheet as DRAFT rows.

Draft rows are never used for flagging (ReferenceRangeService only reads ACTIVE).
A SUPER_ADMIN must explicitly activate them after the lab director has reviewed.
"""
import base64
import io
import re

from flask import Blueprint, request
from sqlalchemy import func

from app.core.audit import write_audit
from app.core.authenticated_identity import authenticated_actor_email
from app.core.authz import roles_required
from app.extensions.db import db
from app.models.reference_range import ReferenceRange

reference_import_bp = Blueprint("reference_import", __name__, url_prefix="/api/v1/reference-ranges-import")

_DRAFT = "DRAFT"
_ACTIVE = "ACTIVE"
_CONFIRM = "TOI XAC NHAN"
_MAX_BYTES = 6 * 1024 * 1024

_COLS = {
    "code": 0, "name": 1, "unit": 7, "sex": 8, "age_from": 9, "age_to": 10,
    "low": 11, "high": 12, "text": 13, "source": 14,
}


def _num(value):
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _age(value):
    n = _num(value)
    return None if n is None else int(n)


def parse_workbook(raw: bytes):
    """Return (rows_to_insert, report). Pure function: no database access."""
    import openpyxl

    wb = openpyxl.load_workbook(io.BytesIO(raw), read_only=True, data_only=True)
    ws = wb[wb.sheetnames[0]]
    rows, warnings = [], []
    total = text_only = no_range = 0
    for idx, r in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
        if not r or not r[0]:
            continue
        total += 1
        code = str(r[_COLS["code"]]).strip()
        low, high = _num(r[_COLS["low"]]), _num(r[_COLS["high"]])
        text = (r[_COLS["text"]] or "").strip() if isinstance(r[_COLS["text"]], str) else ""
        if low is None and high is None:
            if text:
                text_only += 1
            else:
                no_range += 1
            continue
        if low is not None and high is not None and low > high:
            warnings.append(f"Dòng {idx} ({code}): low > high, bỏ qua.")
            continue
        m = re.match(r"\s*<=?\s*([\d.]+)\s*(?:[^\d.\-].*)?$", text)
        if m and high is not None:
            try:
                if abs(float(m.group(1)) - high) > 1e-9:
                    warnings.append(f"Dòng {idx} ({code}): chữ ghi '{text}' nhưng cột high = {high}.")
            except ValueError:
                pass
        if m and low is not None and not text.startswith("<="):
            warnings.append(f"Dòng {idx} ({code}): chữ ghi '{text}' nhưng có cột low = {low}.")
        if not r[_COLS["source"]]:
            warnings.append(f"Dòng {idx} ({code}): không có nguồn.")
        sex = str(r[_COLS["sex"]] or "ALL").strip().upper()
        if sex not in ("M", "F", "ALL"):
            sex = "ALL"
        a_from, a_to = _age(r[_COLS["age_from"]]), _age(r[_COLS["age_to"]])
        rows.append(
            ReferenceRange(
                test_code=code[:50],
                test_name=str(r[_COLS["name"]] or "")[:255],
                sex=sex,
                age_min=0 if a_from is None else a_from,
                age_max=120 if a_to is None else a_to,
                unit=(str(r[_COLS["unit"]])[:50] if r[_COLS["unit"]] else None),
                low_value=low,
                high_value=high,
                status=_DRAFT,
            )
        )
    wb.close()
    return rows, {
        "rows_in_file": total,
        "importable": len(rows),
        "text_only_skipped": text_only,
        "no_range_skipped": no_range,
        "warnings": warnings[:50],
        "warnings_total": len(warnings),
    }


def _counts():
    return {
        (s or "").upper(): int(n)
        for s, n in db.session.query(ReferenceRange.status, func.count(ReferenceRange.id)).group_by(ReferenceRange.status)
    }


@reference_import_bp.route("", methods=["GET"])
@roles_required("SUPER_ADMIN", "SYSTEM_ADMIN")
def status():
    return {"success": True, "counts": _counts()}


@reference_import_bp.route("", methods=["POST"])
@roles_required("SUPER_ADMIN", "SYSTEM_ADMIN")
def import_draft():
    body = request.get_json(silent=True) or {}
    try:
        raw = base64.b64decode(body.get("file_b64") or "", validate=False)
    except Exception:
        return {"success": False, "error": "File không đọc được."}, 400
    if not raw or len(raw) > _MAX_BYTES:
        return {"success": False, "error": "File trống hoặc quá lớn."}, 400
    try:
        rows, report = parse_workbook(raw)
    except Exception:
        return {"success": False, "error": "Không đọc được file Excel (.xlsx)."}, 400
    apply = bool(body.get("apply"))
    report["applied"] = False
    if apply:
        removed = ReferenceRange.query.filter_by(status=_DRAFT).delete()
        db.session.add_all(rows)
        write_audit(
            action="REFERENCE_RANGES_DRAFT_IMPORTED",
            object_type="ReferenceRange",
            object_id="bulk",
            user_email=authenticated_actor_email(),
        )
        db.session.commit()
        report["applied"] = True
        report["replaced_drafts"] = removed
    report["counts"] = _counts()
    return {"success": True, "report": report}


@reference_import_bp.route("/activate", methods=["POST"])
@roles_required("SUPER_ADMIN")
def activate():
    body = request.get_json(silent=True) or {}
    if (body.get("confirm") or "").strip().upper() != _CONFIRM:
        return {"success": False, "error": f"Cần gõ đúng cụm xác nhận: {_CONFIRM}"}, 400
    draft_codes = [c for (c,) in db.session.query(ReferenceRange.test_code).filter_by(status=_DRAFT).distinct()]
    if not draft_codes:
        return {"success": False, "error": "Không có bản nháp để kích hoạt."}, 409
    superseded = (
        ReferenceRange.query.filter(ReferenceRange.status == _ACTIVE, ReferenceRange.test_code.in_(draft_codes))
        .update({"status": "INACTIVE"}, synchronize_session=False)
    )
    activated = ReferenceRange.query.filter_by(status=_DRAFT).update({"status": _ACTIVE}, synchronize_session=False)
    write_audit(
        action="REFERENCE_RANGES_ACTIVATED",
        object_type="ReferenceRange",
        object_id="bulk",
        user_email=authenticated_actor_email(),
    )
    db.session.commit()
    return {"success": True, "activated": activated, "superseded": superseded, "counts": _counts()}
