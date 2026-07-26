"""Reception receipt PDF renderer (ReportLab) — cash-desk receipts."""

from __future__ import annotations

import io
from datetime import datetime
from pathlib import Path
from typing import Any

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

RECEIPT_PDF_TEMPLATE_VERSION = "1.0.0"
RECEIPT_PDF_TEMPLATE_ID = "dxcon-reception-receipt-v1"


class ReceiptPdfError(RuntimeError):
    pass


def default_receipt_pdf_dir() -> Path:
    root = Path(__file__).resolve().parents[2]
    path = root / "uploads" / "receipts"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _fmt_money(value: Any) -> str:
    try:
        return f"{float(value):,.0f} VND"
    except (TypeError, ValueError):
        return "—" if value is None else str(value)


def _fmt_dt(value: Any) -> str:
    if value is None:
        return "—"
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M")
    return str(value)[:19].replace("T", " ")


def build_receipt_pdf_bytes(payload: dict[str, Any]) -> bytes:
    buffer = io.BytesIO()
    # 80mm thermal-like width centered on A4 for printer compatibility
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    left = (width - 80 * mm) / 2
    y = height - 20 * mm

    def line(text: str, *, bold: bool = False, size: int = 10):
        nonlocal y
        pdf.setFont("Helvetica-Bold" if bold else "Helvetica", size)
        pdf.drawString(left, y, text[:64])
        y -= 5 * mm

    line("DxCon Reception Receipt", bold=True, size=12)
    line(f"Template {RECEIPT_PDF_TEMPLATE_ID}@{RECEIPT_PDF_TEMPLATE_VERSION}", size=7)
    y -= 2 * mm
    line(f"Receipt: {payload.get('receipt_code') or '—'}", bold=True)
    line(f"Status: {payload.get('status') or '—'}")
    line(f"Order: {payload.get('order_code') or '—'}")
    line(f"Patient: {payload.get('patient_name') or '—'} ({payload.get('patient_code') or '—'})")
    line(f"Method: {payload.get('payment_method') or '—'}")
    line(f"Amount: {_fmt_money(payload.get('amount'))}", bold=True)
    line(f"Paid at: {_fmt_dt(payload.get('paid_at'))}")
    line(f"Cashier: {payload.get('cashier') or '—'}")
    line(f"Print #: {payload.get('print_count') or 0}")
    if payload.get("reprint"):
        line("*** REPRINT ***", bold=True)
    if payload.get("status") == "cancelled":
        line("*** CANCELLED ***", bold=True)
        if payload.get("cancel_reason"):
            line(f"Reason: {payload.get('cancel_reason')}", size=8)
    y -= 3 * mm
    line("Thank you", size=9)
    pdf.showPage()
    pdf.save()
    data = buffer.getvalue()
    if not data.startswith(b"%PDF"):
        raise ReceiptPdfError("PDF renderer produced invalid output")
    return data


def write_receipt_pdf(payload: dict[str, Any], *, receipt_code: str, reprint: int = 0) -> Path:
    safe = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in receipt_code)
    dest = default_receipt_pdf_dir() / f"{safe}_r{reprint}.pdf"
    dest.write_bytes(build_receipt_pdf_bytes({**payload, "reprint": reprint > 0, "print_count": reprint}))
    return dest
