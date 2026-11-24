"""Shared bulk price entry: parse pasted lines or an uploaded Excel/CSV form, then apply to a price table."""

from __future__ import annotations

import csv
import io

from sqlalchemy import func

from app.clinic_billing.logic import MAX_BULK_LINES, parse_price_lines
from app.extensions.db import db
from app.models.test_catalog import TestCatalog

MAX_UPLOAD_BYTES = 2 * 1024 * 1024
_HEADER_CODES = {"mã", "ma", "code", "mã xn", "mã xét nghiệm", "ma xet nghiem", "mã xét nghiệm (không sửa)"}


def build_template_xlsx(price_header: str, rows: list[tuple[str, str, float, float | None]]) -> bytes:
    """Form with every test: code, name, public price, and an empty (or current) price column to fill in."""
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill

    wb = Workbook()
    ws = wb.active
    ws.title = "Bảng giá"
    ws.append(["Mã xét nghiệm (không sửa)", "Tên xét nghiệm", "Giá public", price_header])
    for cell in ws[1]:
        cell.font = Font(bold=True)
    ws["D1"].fill = PatternFill("solid", fgColor="FFF2CC")
    for code, name, listed, current in rows:
        ws.append([code, name, listed or 0, current if current is not None else None])
    ws.column_dimensions["A"].width = 26
    ws.column_dimensions["B"].width = 48
    ws.column_dimensions["C"].width = 14
    ws.column_dimensions["D"].width = 22
    ws.freeze_panes = "A2"
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def _cell_text(value) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and value.is_integer():
        value = int(value)
    return str(value).strip()


def sheet_to_text(filename: str, data: bytes) -> str:
    """Turn an uploaded form into 'code<TAB>price' lines. Rows with an empty price column are left unchanged."""
    name = (filename or "").lower()
    rows: list[list[str]] = []
    if name.endswith((".xlsx", ".xlsm")):
        from openpyxl import load_workbook

        wb = load_workbook(io.BytesIO(data), read_only=True, data_only=True)
        for r in wb.worksheets[0].iter_rows(values_only=True):
            rows.append([_cell_text(c) for c in r])
    else:
        text = data.decode("utf-8-sig", errors="replace")
        first = text.splitlines()[0] if text.strip() else ""
        delimiter = "\t" if "\t" in first else (";" if ";" in first else ",")
        for r in csv.reader(io.StringIO(text), delimiter=delimiter):
            rows.append([c.strip() for c in r])
    lines: list[str] = []
    for i, cells in enumerate(rows):
        if not cells or not cells[0]:
            continue
        if i == 0 and cells[0].lower() in _HEADER_CODES:
            continue
        price = cells[3] if len(cells) >= 4 else (cells[1] if len(cells) >= 2 else "")
        if not price:
            continue
        lines.append(f"{cells[0]}\t{price}")
    return "\n".join(lines)


def apply_bulk(text: str, org_id: str, model, value_attr: str, actor: str | None, apply: bool) -> tuple[dict | None, str | None]:
    """Create/update/remove rows of `model` (organization_id, test_catalog_id, <value_attr>) from parsed lines."""
    rows = parse_price_lines(text)
    if not rows:
        return None, "Chưa có dòng nào. Mỗi dòng gồm mã xét nghiệm và giá."
    codes = {r["code"].upper() for r in rows if not r["error"]}
    tests: dict[str, TestCatalog] = {}
    if codes:
        for t in TestCatalog.query.filter(func.upper(TestCatalog.code).in_(list(codes))).all():
            tests.setdefault(t.code.upper(), t)
    existing = {p.test_catalog_id: p for p in model.query.filter_by(organization_id=org_id)}
    created = updated = removed = 0
    errors: list[dict] = []
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
                row = model(organization_id=org_id, test_catalog_id=test.id, updated_by=actor)
                setattr(row, value_attr, r["price"])
                db.session.add(row)
                existing[test.id] = row
        else:
            updated += 1
            if apply:
                setattr(row, value_attr, r["price"])
                row.updated_by = actor
    return {
        "applied": apply,
        "created": created,
        "updated": updated,
        "removed": removed,
        "errors": errors,
        "changed": bool(created or updated or removed),
    }, None


def template_rows(current: dict[str, float]) -> list[tuple[str, str, float, float | None]]:
    tests = TestCatalog.query.order_by(TestCatalog.name).all()
    return [(t.code, t.name, t.price or 0, current.get(t.id)) for t in tests]
