"""Report generation engine — Sprint 008."""

from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime
from typing import Any

from app.models.biz_order import BizCollection, BizOrder, BizResult, BizResultItem
from app.models.lab_lis import LabAccessionRecord
from app.models.patient import Patient


def generate_report_code() -> str:
    return f"RPT-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"


def generate_report_hash(payload: dict[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def generate_qr_payload(report_code: str) -> str:
    return f"dxcon:report:{report_code}"


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
    }


def render_html_report(payload: dict[str, Any], *, report_code: str, doctor_note: str | None = None) -> str:
    patient = payload.get("patient", {})
    order = payload.get("order", {})
    collection = payload.get("collection") or {}
    accession = payload.get("accession") or {}
    rows = ""
    for item in payload.get("items", []):
        rows += (
            f"<tr><td>{item.get('test_name')}</td><td>{item.get('result_value')} {item.get('unit') or ''}</td>"
            f"<td>{item.get('reference_range') or '—'}</td><td>{item.get('flag') or '—'}</td>"
            f"<td>{item.get('instrument') or '—'}</td></tr>"
        )
    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Report {report_code}</title>
<style>body{{font-family:Inter,sans-serif;margin:24px;color:#0f172a}}
.header{{border-bottom:2px solid #0ea5e9;padding-bottom:12px;margin-bottom:20px}}
table{{border-collapse:collapse;width:100%}}td,th{{border:1px solid #cbd5e1;padding:8px;text-align:left}}
.footer{{margin-top:24px;font-size:12px;color:#64748b}}</style></head><body>
<div class="header"><h1>DxCon Diagnostic Report</h1>
<p>Report: {report_code} · QR: dxcon:report:{report_code}</p>
<p>Laboratory: DxCon Central Lab · Barcode: {order.get('barcode_value') or '—'}</p></div>
<h2>Patient</h2><p>{patient.get('full_name')} · {patient.get('patient_code')} · DOB {patient.get('date_of_birth') or '—'} · {patient.get('gender') or '—'}</p>
<h2>Order</h2><p>Order: {order.get('order_code')} · Sample: {collection.get('sample_code') or '—'} · Accession: {accession.get('accession_number') or collection.get('accession_number') or '—'}</p>
<p>Collected: {collection.get('scheduled_at') or '—'} · Received: {collection.get('received_at') or '—'}</p>
<h2>Results</h2>
<table><tr><th>Test</th><th>Result</th><th>Reference</th><th>Flag</th><th>Analyzer</th></tr>{rows}</table>
<p><strong>Doctor note:</strong> {doctor_note or '—'}</p>
<div class="footer"><p>Digital signature placeholder · Approved electronically · For clinical use only.</p></div>
</body></html>"""


def prepare_pdf_payload(payload: dict[str, Any], html: str) -> dict[str, Any]:
    return {
        "format": "html_for_pdf",
        "page_size": "A4",
        "html_length": len(html),
        "item_count": len(payload.get("items", [])),
        "ready": True,
    }
