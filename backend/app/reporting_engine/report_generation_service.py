"""Report generation engine — Sprint 008 + Production Report PDF."""

from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime
from typing import Any

from flask import current_app, has_request_context, request

from app.models.biz_order import BizCollection, BizOrder, BizResult
from app.models.lab_lis import LabAccessionRecord
from app.models.patient import Patient
from app.reporting_engine.pdf_service import REPORT_PDF_TEMPLATE_ID, REPORT_PDF_TEMPLATE_VERSION

REPORT_HTML_TEMPLATE_VERSION = REPORT_PDF_TEMPLATE_VERSION


def generate_report_code() -> str:
    return f"RPT-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"


def generate_report_hash(payload: dict[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def generate_qr_payload(report_code: str) -> str:
    return f"dxcon:report:{report_code}"


def build_verify_url(report_code: str, report_hash: str | None = None) -> str:
    """Public verification URL for QR codes."""
    path = f"/results/verify/report/{report_code}"
    if report_hash:
        path = f"{path}?hash={report_hash[:16]}"
    if has_request_context():
        try:
            return request.url_root.rstrip("/") + path
        except Exception:
            pass
    try:
        base = (current_app.config.get("PUBLIC_BASE_URL") or "").rstrip("/")
        if base:
            return f"{base}{path}"
    except Exception:
        pass
    return path


def build_report_payload(order_id: str) -> dict[str, Any]:
    order = BizOrder.query.get(order_id) if len(order_id) == 36 else None
    if not order:
        order = BizOrder.query.filter_by(order_code=order_id).first()
    if not order:
        raise ValueError("Order not found")
    patient = Patient.query.get(order.patient_code)
    collection = BizCollection.query.filter_by(order_id=order.id).first()
    result = BizResult.query.filter_by(order_id=order.id).first()
    accession = LabAccessionRecord.query.filter_by(order_code=order.order_code).first()
    items = []
    abnormal_count = critical_count = 0
    if result:
        for item in result.items:
            flag = (item.flag or "NORMAL").upper()
            if flag not in ("NORMAL", ""):
                abnormal_count += 1
            if "CRITICAL" in flag:
                critical_count += 1
            items.append({
                "test_code": item.test_code,
                "test_name": item.test_name,
                "result_value": item.result_value,
                "unit": item.unit,
                "reference_range": item.reference_range,
                "flag": item.flag,
                "instrument": getattr(item, "instrument", None),
                "technician": getattr(item, "technician", None),
                "result_time": getattr(item, "result_time", None).isoformat()
                if getattr(item, "result_time", None)
                else None,
            })
    return {
        "order": order.to_dict(),
        "patient": patient.to_dict() if patient else {"patient_code": order.patient_code, "full_name": order.patient_name},
        "collection": collection.to_dict() if collection else None,
        "accession": accession.to_dict() if accession else None,
        "result": result.to_dict() if result else None,
        "items": items,
        "abnormal_count": abnormal_count,
        "critical_count": critical_count,
        "organization": {"name": "DxCon Laboratory", "logo_placeholder": True},
        "laboratory": {"name": "DxCon Central Lab"},
        "template": {
            "id": REPORT_PDF_TEMPLATE_ID,
            "version": REPORT_PDF_TEMPLATE_VERSION,
            "html_version": REPORT_HTML_TEMPLATE_VERSION,
        },
    }


def _esc(value: Any) -> str:
    text = str(value if value is not None else "")
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def render_html_report(
    payload: dict[str, Any],
    *,
    report_code: str,
    doctor_note: str | None = None,
    report_version: int = 1,
    report_status: str | None = None,
    report_hash: str | None = None,
    approved_by: str | None = None,
    approved_at: Any = None,
    released_by: str | None = None,
    released_at: Any = None,
    amendment_reason: str | None = None,
    reprint_number: int = 0,
    verify_url: str | None = None,
) -> str:
    """HTML report aligned with PDF content for browser print consistency."""
    patient = payload.get("patient", {}) or {}
    order = payload.get("order", {}) or {}
    collection = payload.get("collection") or {}
    accession = payload.get("accession") or {}
    laboratory = payload.get("laboratory") or {}
    abnormal = payload.get("abnormal_count") or 0
    critical = payload.get("critical_count") or 0
    verify = verify_url or build_verify_url(report_code, report_hash)

    banners = ""
    if amendment_reason:
        banners += f'<div class="banner amend">AMENDED / CORRECTED — {_esc(amendment_reason)}</div>'
    if reprint_number and reprint_number > 0:
        banners += f'<div class="banner reprint">REPRINT #{int(reprint_number)} — finalized content unchanged</div>'
    if critical:
        banners += f'<div class="banner critical">CRITICAL RESULTS PRESENT ({critical})</div>'
    elif abnormal:
        banners += f'<div class="banner abnormal">ABNORMAL RESULTS PRESENT ({abnormal})</div>'

    rows = ""
    for item in payload.get("items", []):
        flag = (item.get("flag") or "NORMAL").upper()
        flag_class = "flag-critical" if "CRITICAL" in flag else ("flag-abnormal" if flag not in ("NORMAL", "") else "")
        rows += (
            f"<tr class='{flag_class}'>"
            f"<td>{_esc(item.get('test_name'))}</td>"
            f"<td>{_esc(item.get('result_value'))}</td>"
            f"<td>{_esc(item.get('unit') or '')}</td>"
            f"<td>{_esc(item.get('reference_range') or '—')}</td>"
            f"<td>{_esc(item.get('flag') or '—')}</td>"
            f"<td>{_esc(item.get('technician') or item.get('instrument') or '—')}</td>"
            f"</tr>"
        )
    if not rows:
        rows = "<tr><td colspan='6'>No result items on finalized report.</td></tr>"

    return f"""<!DOCTYPE html>
<html lang="vi"><head><meta charset="utf-8"><title>Report {_esc(report_code)}</title>
<style>
@page {{ size: A4; margin: 14mm; }}
body {{ font-family: "DejaVu Sans", "Noto Sans", Inter, "Segoe UI", sans-serif; margin: 0; color: #0f172a; font-size: 12px; }}
.wrap {{ padding: 8px 4px 24px; }}
.header {{ border-bottom: 2px solid #0ea5e9; padding-bottom: 10px; margin-bottom: 14px; }}
h1 {{ font-size: 18px; margin: 4px 0; }}
h2 {{ font-size: 13px; margin: 16px 0 6px; }}
.meta {{ color: #475569; font-size: 11px; }}
.grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 8px 24px; }}
table {{ border-collapse: collapse; width: 100%; margin-top: 6px; }}
td, th {{ border: 1px solid #cbd5e1; padding: 6px 8px; text-align: left; }}
th {{ background: #f1f5f9; }}
.flag-critical td {{ background: #fef2f2; }}
.flag-abnormal td {{ background: #fff7ed; }}
.banner {{ padding: 6px 10px; margin: 6px 0; font-weight: 700; font-size: 11px; }}
.banner.critical {{ background: #fee2e2; color: #991b1b; }}
.banner.abnormal {{ background: #ffedd5; color: #9a3412; }}
.banner.amend {{ background: #fce7f3; color: #9d174d; }}
.banner.reprint {{ background: #e0e7ff; color: #3730a3; }}
.footer {{ margin-top: 18px; font-size: 10px; color: #64748b; border-top: 1px solid #e2e8f0; padding-top: 8px; }}
@media print {{
  .no-print {{ display: none !important; }}
  body {{ -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
}}
</style></head><body>
<div class="wrap">
<div class="header">
  <div class="meta">{_esc(laboratory.get('name') or 'DxCon Central Lab')} · Template {REPORT_PDF_TEMPLATE_ID} · v{REPORT_HTML_TEMPLATE_VERSION}</div>
  <h1>Diagnostic Laboratory Report</h1>
  <p class="meta">Report: {_esc(report_code)} · Version {int(report_version)} · Status: {_esc((report_status or 'draft').upper())}</p>
  <p class="meta">QR / Verify: {_esc(verify)}</p>
</div>
{banners}
<h2>Patient</h2>
<div class="grid">
  <div><strong>{_esc(patient.get('full_name'))}</strong><br>ID {_esc(patient.get('patient_code') or order.get('patient_code'))}<br>
  DOB {_esc(patient.get('date_of_birth') or '—')} · {_esc(patient.get('gender') or '—')}<br>Phone {_esc(patient.get('phone') or '—')}</div>
  <div>Order <strong>{_esc(order.get('order_code'))}</strong><br>Barcode {_esc(order.get('barcode_value') or '—')}<br>
  Accession {_esc(accession.get('accession_number') or collection.get('accession_number') or '—')}<br>
  Sample {_esc(collection.get('sample_code') or '—')}</div>
</div>
<h2>Timestamps</h2>
<p>Collected: {_esc(collection.get('collected_at') or collection.get('scheduled_at') or '—')} ·
Received: {_esc(collection.get('received_at') or '—')} ·
Reported: {_esc(approved_at or '—')} ·
Released: {_esc(released_at or '—')}</p>
<h2>Results</h2>
<table>
<tr><th>Test</th><th>Result</th><th>Unit</th><th>Reference</th><th>Flag</th><th>Tech / Analyzer</th></tr>
{rows}
</table>
<h2>Clinical authorization</h2>
<p>Validated / approved by: {_esc(approved_by or '—')}<br>
Approved at: {_esc(approved_at or '—')}<br>
Released by: {_esc(released_by or '—')} at {_esc(released_at or '—')}<br>
Doctor note: {_esc(doctor_note or '—')}<br>
Signature method: INTERNAL_APPROVAL · Hash: {_esc((report_hash or '—')[:48])}</p>
<div class="footer">
<p>Electronically signed. Content is immutable for this report version. Privacy: authorized clinical use only.</p>
<p class="no-print"><a href="/api/v1/reporting/reports/{_esc(report_code)}/pdf">Download PDF</a>
 · <a href="javascript:window.print()">Print</a></p>
</div>
</div>
</body></html>"""


def prepare_pdf_payload(
    payload: dict[str, Any],
    html: str,
    *,
    pdf_ready: bool = False,
    pdf_path: str | None = None,
) -> dict[str, Any]:
    return {
        "format": "application/pdf" if pdf_ready else "html_for_pdf",
        "page_size": "A4",
        "template_id": REPORT_PDF_TEMPLATE_ID,
        "template_version": REPORT_PDF_TEMPLATE_VERSION,
        "html_length": len(html),
        "item_count": len(payload.get("items", [])),
        "ready": True,
        "pdf_ready": pdf_ready,
        "pdf_path": pdf_path,
    }
