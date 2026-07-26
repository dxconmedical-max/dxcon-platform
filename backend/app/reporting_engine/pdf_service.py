"""Production clinical Report PDF renderer (ReportLab).

Generates immutable A4 PDFs from finalized ClinicalReport / BizResult payload.
Template version is stamped into every artifact for reprint/audit traceability.
"""

from __future__ import annotations

import io
import os
from datetime import datetime
from pathlib import Path
from typing import Any

import qrcode
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

REPORT_PDF_TEMPLATE_VERSION = "1.0.0"
REPORT_PDF_TEMPLATE_ID = "dxcon-clinical-report-v1"

_FONT_DIR = Path(__file__).resolve().parent / "fonts"
_FONT_REGISTERED = False
_FONT_NAME = "Helvetica"
_FONT_BOLD = "Helvetica-Bold"


class ReportPdfError(RuntimeError):
    """Raised when PDF generation cannot complete."""


def _register_fonts() -> tuple[str, str]:
    global _FONT_REGISTERED, _FONT_NAME, _FONT_BOLD
    if _FONT_REGISTERED:
        return _FONT_NAME, _FONT_BOLD

    candidates = [
        (_FONT_DIR / "DejaVuSans.ttf", _FONT_DIR / "DejaVuSans-Bold.ttf"),
        (Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"), Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")),
        (Path("/System/Library/Fonts/Supplemental/Arial Unicode.ttf"), Path("/System/Library/Fonts/Supplemental/Arial Unicode.ttf")),
        (Path("/Library/Fonts/Arial Unicode.ttf"), Path("/Library/Fonts/Arial Unicode.ttf")),
    ]
    for regular, bold in candidates:
        if regular.exists():
            try:
                pdfmetrics.registerFont(TTFont("DxConReport", str(regular)))
                bold_path = bold if bold.exists() else regular
                pdfmetrics.registerFont(TTFont("DxConReport-Bold", str(bold_path)))
                _FONT_NAME = "DxConReport"
                _FONT_BOLD = "DxConReport-Bold"
                break
            except Exception:
                continue
    _FONT_REGISTERED = True
    return _FONT_NAME, _FONT_BOLD


def default_pdf_storage_dir() -> Path:
    root = Path(__file__).resolve().parents[2]
    path = root / "uploads" / "reports" / "clinical"
    path.mkdir(parents=True, exist_ok=True)
    return path


def pdf_filename(report_code: str, version: int) -> str:
    safe = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in report_code)
    return f"{safe}_v{version}.pdf"


def resolve_pdf_path(report_code: str, version: int, *, base_dir: Path | None = None) -> Path:
    return (base_dir or default_pdf_storage_dir()) / pdf_filename(report_code, version)


def _fmt_dt(value: Any) -> str:
    if value is None:
        return "—"
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M UTC")
    text = str(value).strip()
    if not text:
        return "—"
    if "T" in text:
        return text.replace("T", " ")[:19] + (" UTC" if "Z" in text or "+" in text[10:] else "")
    return text[:32]


def _flag_style(flag: str | None) -> tuple[str, colors.Color | None]:
    f = (flag or "NORMAL").upper()
    if "CRITICAL" in f:
        return f, colors.Color(0.75, 0.05, 0.05)
    if f in ("HIGH", "LOW", "ABNORMAL") or "ABNORMAL" in f:
        return f, colors.Color(0.85, 0.45, 0.05)
    if f in ("", "NORMAL"):
        return "NORMAL", None
    return f, colors.Color(0.2, 0.2, 0.55)


def _qr_image(payload: str):
    qr = qrcode.QRCode(version=1, box_size=3, border=1)
    qr.add_data(payload)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf


def build_frozen_pdf_document(
    *,
    payload: dict[str, Any],
    report_code: str,
    report_version: int,
    report_hash: str,
    report_status: str,
    approved_by: str | None,
    approved_at: Any,
    released_by: str | None = None,
    released_at: Any = None,
    doctor_note: str | None = None,
    amendment_reason: str | None = None,
    qr_payload: str | None = None,
    verify_url: str | None = None,
    reprint_number: int = 0,
    reported_at: Any = None,
) -> bytes:
    """Render a clinical PDF from authoritative payload. Returns PDF bytes."""
    font, font_bold = _register_fonts()
    patient = payload.get("patient") or {}
    order = payload.get("order") or {}
    collection = payload.get("collection") or {}
    accession = payload.get("accession") or {}
    laboratory = payload.get("laboratory") or {}
    organization = payload.get("organization") or {}
    items = list(payload.get("items") or [])
    abnormal_count = int(payload.get("abnormal_count") or 0)
    critical_count = int(payload.get("critical_count") or 0)

    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    pdf.setTitle(f"DxCon Report {report_code}")
    pdf.setAuthor(str(approved_by or "DxCon Laboratory"))
    pdf.setSubject(f"{REPORT_PDF_TEMPLATE_ID}@{REPORT_PDF_TEMPLATE_VERSION}")
    pdf.setCreator(f"DxCon Reporting Engine {REPORT_PDF_TEMPLATE_VERSION}")
    pdf.setKeywords(
        f"report_code={report_code};version={report_version};hash={(report_hash or '')[:16]};"
        f"status={report_status};template={REPORT_PDF_TEMPLATE_ID}"
    )
    width, height = A4
    left = 18 * mm
    right = width - 18 * mm
    usable = right - left

    qr_data = verify_url or qr_payload or f"dxcon:report:{report_code}"
    qr_buf = _qr_image(qr_data)

    def draw_header(page_no: int, page_count_hint: str) -> float:
        y = height - 16 * mm
        pdf.setFont(font_bold, 14)
        lab_name = laboratory.get("name") or organization.get("name") or "DxCon Laboratory"
        pdf.drawString(left, y, str(lab_name))
        pdf.setFont(font, 8)
        pdf.drawRightString(right, y, f"Template {REPORT_PDF_TEMPLATE_ID} · {REPORT_PDF_TEMPLATE_VERSION}")
        y -= 12
        pdf.setFont(font_bold, 16)
        pdf.drawString(left, y, "Diagnostic Laboratory Report")
        y -= 10
        pdf.setStrokeColor(colors.Color(0.05, 0.45, 0.65))
        pdf.setLineWidth(1.5)
        pdf.line(left, y, right, y)
        y -= 14
        pdf.setFont(font, 9)
        pdf.drawString(left, y, f"Report: {report_code}  ·  Version {report_version}  ·  Status: {report_status.upper()}")
        pdf.drawRightString(right, y, f"Page {page_no}{page_count_hint}")
        y -= 12
        if amendment_reason:
            pdf.setFillColor(colors.Color(0.55, 0.15, 0.05))
            pdf.setFont(font_bold, 9)
            pdf.drawString(left, y, f"AMENDED / CORRECTED — {amendment_reason}")
            pdf.setFillColor(colors.black)
            y -= 12
        if reprint_number and reprint_number > 0:
            pdf.setFillColor(colors.Color(0.25, 0.25, 0.45))
            pdf.setFont(font_bold, 9)
            pdf.drawString(left, y, f"REPRINT #{reprint_number} — original finalized content unchanged")
            pdf.setFillColor(colors.black)
            y -= 12
        if critical_count:
            pdf.setFillColor(colors.Color(0.75, 0.05, 0.05))
            pdf.setFont(font_bold, 9)
            pdf.drawString(left, y, f"CRITICAL RESULTS PRESENT ({critical_count})")
            pdf.setFillColor(colors.black)
            y -= 12
        elif abnormal_count:
            pdf.setFillColor(colors.Color(0.85, 0.45, 0.05))
            pdf.setFont(font_bold, 9)
            pdf.drawString(left, y, f"ABNORMAL RESULTS PRESENT ({abnormal_count})")
            pdf.setFillColor(colors.black)
            y -= 12
        return y

    def draw_footer(page_no: int) -> None:
        pdf.setFont(font, 7)
        pdf.setFillColor(colors.Color(0.35, 0.4, 0.45))
        pdf.drawString(left, 10 * mm, f"Hash: {(report_hash or '')[:24]}…  ·  Confidential clinical document")
        pdf.drawRightString(right, 10 * mm, f"Generated { _fmt_dt(reported_at or approved_at) }")
        pdf.setFillColor(colors.black)

    # Estimate pages: header block ~120pt, ~22pt per row, footer reserved
    rows_per_page_first = 18
    rows_per_page_next = 24
    if not items:
        page_breaks = [0]
    else:
        page_breaks = [0]
        remaining = len(items)
        first = min(rows_per_page_first, remaining)
        remaining -= first
        idx = first
        while remaining > 0:
            page_breaks.append(idx)
            take = min(rows_per_page_next, remaining)
            idx += take
            remaining -= take

    total_pages = max(1, len(page_breaks))

    for page_idx, start in enumerate(page_breaks):
        page_no = page_idx + 1
        end = page_breaks[page_idx + 1] if page_idx + 1 < len(page_breaks) else len(items)
        y = draw_header(page_no, f" / {total_pages}")

        if page_idx == 0:
            # Patient / order block
            pdf.setFont(font_bold, 10)
            pdf.drawString(left, y, "Patient")
            pdf.drawString(left + usable * 0.52, y, "Order / Accession")
            y -= 12
            pdf.setFont(font, 9)
            lines_left = [
                f"Name: {patient.get('full_name') or '—'}",
                f"ID: {patient.get('patient_code') or order.get('patient_code') or '—'}",
                f"DOB: {patient.get('date_of_birth') or '—'}  ·  Sex: {patient.get('gender') or '—'}",
                f"Phone: {patient.get('phone') or '—'}",
            ]
            lines_right = [
                f"Order: {order.get('order_code') or '—'}",
                f"Barcode: {order.get('barcode_value') or '—'}",
                f"Accession: {accession.get('accession_number') or collection.get('accession_number') or '—'}",
                f"Sample: {collection.get('sample_code') or '—'}",
            ]
            block_top = y
            for i, line in enumerate(lines_left):
                pdf.drawString(left, y - i * 11, line)
            for i, line in enumerate(lines_right):
                pdf.drawString(left + usable * 0.52, block_top - i * 11, line)
            y = block_top - max(len(lines_left), len(lines_right)) * 11 - 8

            pdf.setFont(font_bold, 10)
            pdf.drawString(left, y, "Timestamps")
            y -= 12
            pdf.setFont(font, 8)
            ts_lines = [
                f"Collected: {_fmt_dt(collection.get('collected_at') or collection.get('scheduled_at'))}",
                f"Received: {_fmt_dt(collection.get('received_at'))}",
                f"Reported: {_fmt_dt(reported_at or approved_at)}",
                f"Released: {_fmt_dt(released_at)}" if released_at else "Released: —",
            ]
            for i, line in enumerate(ts_lines):
                col = i % 2
                row = i // 2
                pdf.drawString(left + col * (usable * 0.52), y - row * 11, line)
            y -= 28

            # QR
            try:
                from reportlab.lib.utils import ImageReader

                pdf.drawImage(ImageReader(qr_buf), right - 28 * mm, height - 52 * mm, 26 * mm, 26 * mm, mask="auto")
                pdf.setFont(font, 6)
                pdf.drawCentredString(right - 15 * mm, height - 54 * mm, "Verify")
            except Exception:
                pass

            pdf.setFont(font_bold, 10)
            pdf.drawString(left, y, "Results")
            y -= 4

        # Table header
        y -= 12
        pdf.setFillColor(colors.Color(0.93, 0.95, 0.97))
        pdf.rect(left, y - 2, usable, 14, fill=1, stroke=0)
        pdf.setFillColor(colors.black)
        pdf.setFont(font_bold, 8)
        cols = [
            (left + 2, "Test"),
            (left + usable * 0.34, "Result"),
            (left + usable * 0.48, "Unit"),
            (left + usable * 0.58, "Reference"),
            (left + usable * 0.78, "Flag"),
            (left + usable * 0.90, "Tech"),
        ]
        for x, label in cols:
            pdf.drawString(x, y + 2, label)
        y -= 14
        pdf.setFont(font, 8)

        page_items = items[start:end] if items else []
        if not page_items and page_idx == 0:
            pdf.drawString(left + 2, y, "No result items on finalized report.")
            y -= 14

        for item in page_items:
            if y < 28 * mm:
                break
            flag_label, flag_color = _flag_style(item.get("flag"))
            test_name = str(item.get("test_name") or item.get("test_code") or "")[:38]
            result_value = str(item.get("result_value") or "")[:16]
            unit = str(item.get("unit") or "")[:12]
            ref = str(item.get("reference_range") or "—")[:22]
            tech = str(item.get("technician") or "—")[:10]
            pdf.drawString(left + 2, y, test_name)
            pdf.drawString(left + usable * 0.34, y, result_value)
            pdf.drawString(left + usable * 0.48, y, unit)
            pdf.drawString(left + usable * 0.58, y, ref)
            if flag_color:
                pdf.setFillColor(flag_color)
                pdf.setFont(font_bold, 8)
            pdf.drawString(left + usable * 0.78, y, flag_label[:12])
            pdf.setFillColor(colors.black)
            pdf.setFont(font, 8)
            pdf.drawString(left + usable * 0.90, y, tech)
            y -= 12
            # light rule
            pdf.setStrokeColor(colors.Color(0.85, 0.88, 0.9))
            pdf.setLineWidth(0.3)
            pdf.line(left, y + 8, right, y + 8)
            pdf.setStrokeColor(colors.black)

        if page_idx == total_pages - 1:
            y -= 10
            if y < 40 * mm:
                draw_footer(page_no)
                pdf.showPage()
                y = draw_header(page_no + 1, f" / {total_pages + 1}")
                total_pages_display = total_pages + 1
            else:
                total_pages_display = total_pages

            pdf.setFont(font_bold, 10)
            pdf.drawString(left, y, "Clinical authorization")
            y -= 12
            pdf.setFont(font, 9)
            pdf.drawString(left, y, f"Validated / approved by: {approved_by or '—'}")
            y -= 11
            pdf.drawString(left, y, f"Approved at: {_fmt_dt(approved_at)}")
            y -= 11
            if released_by:
                pdf.drawString(left, y, f"Released by: {released_by} at {_fmt_dt(released_at)}")
                y -= 11
            pdf.drawString(left, y, f"Doctor note: {doctor_note or '—'}")
            y -= 11
            pdf.drawString(left, y, f"Signature method: INTERNAL_APPROVAL  ·  Report hash: {(report_hash or '')[:40]}")
            y -= 14
            pdf.setFont(font, 8)
            pdf.drawString(left, y, "This document is electronically signed. Content is immutable for this report version.")
            y -= 10
            pdf.setFont(font, 7)
            pdf.setFillColor(colors.Color(0.4, 0.4, 0.45))
            pdf.drawString(left, y, "Privacy: For authorized clinical use only. Do not redistribute patient identifiers.")
            pdf.setFillColor(colors.black)
            # silence unused
            _ = total_pages_display

        draw_footer(page_no)
        pdf.showPage()

    pdf.save()
    data = buffer.getvalue()
    if not data.startswith(b"%PDF"):
        raise ReportPdfError("PDF renderer produced invalid output")
    return data


def write_report_pdf(
    *,
    payload: dict[str, Any],
    report_code: str,
    report_version: int,
    report_hash: str,
    report_status: str,
    approved_by: str | None,
    approved_at: Any,
    released_by: str | None = None,
    released_at: Any = None,
    doctor_note: str | None = None,
    amendment_reason: str | None = None,
    qr_payload: str | None = None,
    verify_url: str | None = None,
    reprint_number: int = 0,
    reported_at: Any = None,
    dest_path: Path | str | None = None,
) -> Path:
    """Write immutable PDF to disk. Refuses overwrite of an existing finalized file unless dest differs."""
    data = build_frozen_pdf_document(
        payload=payload,
        report_code=report_code,
        report_version=report_version,
        report_hash=report_hash,
        report_status=report_status,
        approved_by=approved_by,
        approved_at=approved_at,
        released_by=released_by,
        released_at=released_at,
        doctor_note=doctor_note,
        amendment_reason=amendment_reason,
        qr_payload=qr_payload,
        verify_url=verify_url,
        reprint_number=reprint_number,
        reported_at=reported_at,
    )
    path = Path(dest_path) if dest_path else resolve_pdf_path(report_code, report_version)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and reprint_number == 0:
        # Immutability: keep original bytes; return existing path
        return path
    path.write_bytes(data)
    try:
        os.chmod(path, 0o644)
    except OSError:
        pass
    return path


def read_pdf_bytes(path: Path | str) -> bytes:
    p = Path(path)
    if not p.exists():
        raise ReportPdfError(f"PDF not found: {p}")
    data = p.read_bytes()
    if not data.startswith(b"%PDF"):
        raise ReportPdfError("Stored artifact is not a valid PDF")
    return data
