"""Small helper to send tabular data as an Excel download."""

from __future__ import annotations

import io
import re
import unicodedata

from flask import Response

XLSX_MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def safe_filename(text: str, fallback: str = "bao-cao") -> str:
    ascii_text = unicodedata.normalize("NFKD", (text or "").replace("đ", "d").replace("Đ", "D")).encode("ascii", "ignore").decode()
    slug = re.sub(r"[^A-Za-z0-9._-]+", "-", ascii_text).strip("-")
    return slug or fallback


def _safe_cell(value):
    """Stop spreadsheet formula injection from user-entered text (=, +, -, @ at the start)."""
    if isinstance(value, str) and value[:1] in ("=", "+", "-", "@"):
        return "'" + value
    return value


def build_xlsx(sheets: list[tuple[str, list[str], list[list]]], money_cols: dict[str, set[int]] | None = None) -> bytes:
    """sheets = [(title, header, rows)]; money_cols maps title -> 0-based column indexes shown as 1,234,567."""
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill

    wb = Workbook()
    wb.remove(wb.active)
    for title, header, rows in sheets:
        ws = wb.create_sheet(title[:31])
        ws.append(header)
        for cell in ws[1]:
            cell.font = Font(bold=True)
            cell.fill = PatternFill("solid", fgColor="E2F0EE")
        for r in rows:
            ws.append([_safe_cell(v) for v in r])
        for i, col in enumerate(header):
            width = max([len(str(col))] + [len(str(r[i])) for r in rows[:200] if i < len(r) and r[i] is not None])
            ws.column_dimensions[ws.cell(row=1, column=i + 1).column_letter].width = min(max(width + 2, 10), 60)
        for idx in (money_cols or {}).get(title, set()):
            for row in ws.iter_rows(min_row=2, min_col=idx + 1, max_col=idx + 1):
                for cell in row:
                    cell.number_format = "#,##0"
        ws.freeze_panes = "A2"
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def xlsx_response(data: bytes, filename: str) -> Response:
    return Response(
        data,
        mimetype=XLSX_MIME,
        headers={"Content-Disposition": f'attachment; filename="{safe_filename(filename.removesuffix(".xlsx"))}.xlsx"'},
    )
