"""Reception Receipt Engine — issue, preview, print, PDF, reprint, cancel.

Reuses BizPayment / BizOrder; does not duplicate payment collection logic.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
import uuid

from sqlalchemy import or_

from app.extensions.db import db
from app.models.biz_order import BizInvoice, BizOrder, BizPayment, BizReceipt
from app.reception_workspace.audit import write_reception_audit
from app.reception_workspace.errors import ReceptionWorkspaceError
from app.reception_workspace.receipt_pdf import (
    RECEIPT_PDF_TEMPLATE_ID,
    RECEIPT_PDF_TEMPLATE_VERSION,
    build_receipt_pdf_bytes,
    write_receipt_pdf,
)

RECEIPT_STATUS_ISSUED = "issued"
RECEIPT_STATUS_REPRINTED = "reprinted"
RECEIPT_STATUS_CANCELLED = "cancelled"

RECEIPT_FORMAT_STANDARD = "standard"
RECEIPT_FORMAT_THERMAL = "thermal"


def _utcnow_naive() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _code(prefix: str) -> str:
    return f"{prefix}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6].upper()}"


def _get_payment(payment_ref: str) -> BizPayment:
    payment = BizPayment.query.filter(
        or_(BizPayment.id == payment_ref, BizPayment.receipt_number == payment_ref)
    ).first()
    if not payment:
        raise ReceptionWorkspaceError("Payment not found")
    return payment


def _get_receipt(receipt_ref: str) -> BizReceipt:
    receipt = BizReceipt.query.filter(
        or_(BizReceipt.id == receipt_ref, BizReceipt.receipt_code == receipt_ref)
    ).first()
    if not receipt:
        raise ReceptionWorkspaceError("Receipt not found")
    return receipt


def _order_for_payment(payment: BizPayment) -> BizOrder:
    order = BizOrder.query.get(payment.order_id)
    if not order:
        raise ReceptionWorkspaceError("Order not found for payment")
    return order


def _context_payload(payment: BizPayment, receipt: BizReceipt | None = None) -> dict[str, Any]:
    order = _order_for_payment(payment)
    invoice = BizInvoice.query.get(payment.invoice_id) if payment.invoice_id else None
    return {
        "receipt_code": receipt.receipt_code if receipt else payment.receipt_number,
        "status": receipt.status if receipt else RECEIPT_STATUS_ISSUED,
        "order_code": order.order_code,
        "patient_code": order.patient_code,
        "patient_name": order.patient_name,
        "payment_method": payment.payment_method,
        "amount": payment.amount,
        "paid_at": payment.paid_at.isoformat() if payment.paid_at else None,
        "cashier": payment.created_by or (receipt.issued_by if receipt else None),
        "invoice_no": invoice.invoice_no if invoice else None,
        "print_count": int(receipt.print_count or 0) if receipt else 0,
        "cancel_reason": receipt.cancel_reason if receipt else None,
        "template_id": RECEIPT_PDF_TEMPLATE_ID,
        "template_version": RECEIPT_PDF_TEMPLATE_VERSION,
    }


def render_receipt_html(payload: dict[str, Any], *, thermal: bool = False) -> str:
    width = "80mm" if thermal else "420px"
    font = "12px" if thermal else "14px"
    reprint = "REPRINT" if payload.get("reprint") else ""
    cancelled = "CANCELLED" if payload.get("status") == "cancelled" else ""
    return f"""<!doctype html>
<html><head><meta charset="utf-8"/><title>Receipt {payload.get('receipt_code') or ''}</title>
<style>
@page {{ size: {width} auto; margin: 4mm; }}
body {{ font-family: ui-monospace, Menlo, monospace; font-size: {font}; width: {width}; margin: 0 auto; color: #111; }}
h1 {{ font-size: 1.1em; margin: 0 0 8px; }}
.row {{ display: flex; justify-content: space-between; margin: 4px 0; gap: 8px; }}
.hr {{ border-top: 1px dashed #94a3b8; margin: 10px 0; }}
.badge {{ font-weight: 700; letter-spacing: .04em; }}
</style></head><body>
<h1>DxCon Reception Receipt</h1>
{f'<div class="badge">{reprint}</div>' if reprint else ''}
{f'<div class="badge">{cancelled}</div>' if cancelled else ''}
<div class="row"><span>Receipt</span><span>{_esc(payload.get('receipt_code'))}</span></div>
<div class="row"><span>Order</span><span>{_esc(payload.get('order_code'))}</span></div>
<div class="row"><span>Patient</span><span>{_esc(payload.get('patient_name'))} ({_esc(payload.get('patient_code'))})</span></div>
<div class="hr"></div>
<div class="row"><span>Method</span><span>{_esc(payload.get('payment_method'))}</span></div>
<div class="row"><span>Amount</span><span>{_esc(_money(payload.get('amount')))}</span></div>
<div class="row"><span>Paid at</span><span>{_esc(str(payload.get('paid_at') or '—')[:19].replace('T',' '))}</span></div>
<div class="row"><span>Cashier</span><span>{_esc(payload.get('cashier') or '—')}</span></div>
<div class="row"><span>Print #</span><span>{_esc(payload.get('print_count') or 0)}</span></div>
{f'<div class="row"><span>Cancel</span><span>{_esc(payload.get("cancel_reason"))}</span></div>' if payload.get('cancel_reason') else ''}
<div class="hr"></div>
<p>Thank you</p>
</body></html>"""


def render_thermal_payload(payload: dict[str, Any]) -> str:
    """Plain-text ESC/POS-friendly receipt body (no binary ESC sequences)."""
    lines = [
        "DxCon Reception",
        "----------------",
        f"RCT: {payload.get('receipt_code') or '—'}",
        f"ORD: {payload.get('order_code') or '—'}",
        f"PT:  {payload.get('patient_name') or '—'} ({payload.get('patient_code') or '—'})",
        f"PAY: {payload.get('payment_method') or '—'}",
        f"AMT: {_money(payload.get('amount'))}",
        f"AT:  {str(payload.get('paid_at') or '—')[:19].replace('T', ' ')}",
        f"BY:  {payload.get('cashier') or '—'}",
        f"PRINT:{payload.get('print_count') or 0}",
    ]
    if payload.get("reprint"):
        lines.append("*** REPRINT ***")
    if payload.get("status") == "cancelled":
        lines.append("*** CANCELLED ***")
        if payload.get("cancel_reason"):
            lines.append(f"REASON: {payload.get('cancel_reason')}")
    lines.extend(["----------------", "Thank you", ""])
    return "\n".join(lines)


def _esc(value: Any) -> str:
    text = "" if value is None else str(value)
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _money(value: Any) -> str:
    try:
        return f"{float(value):,.0f} VND"
    except (TypeError, ValueError):
        return "—"


def issue_receipt_for_payment(
    payment_ref: str,
    *,
    preferred_format: str = RECEIPT_FORMAT_STANDARD,
    actor: str | None = None,
) -> BizReceipt:
    payment = _get_payment(payment_ref)
    existing = BizReceipt.query.filter_by(payment_id=payment.id).first()
    if existing:
        return existing
    if preferred_format not in {RECEIPT_FORMAT_STANDARD, RECEIPT_FORMAT_THERMAL}:
        preferred_format = RECEIPT_FORMAT_STANDARD

    receipt = BizReceipt(
        receipt_code=payment.receipt_number or _code("RCT"),
        payment_id=payment.id,
        order_id=payment.order_id,
        invoice_id=payment.invoice_id,
        status=RECEIPT_STATUS_ISSUED,
        print_count=0,
        preferred_format=preferred_format,
        issued_at=_utcnow_naive(),
        issued_by=actor or payment.created_by,
    )
    ctx = _context_payload(payment, receipt)
    receipt.html_snapshot = render_receipt_html(ctx, thermal=False)
    receipt.thermal_payload = render_thermal_payload(ctx)
    db.session.add(receipt)
    db.session.flush()
    write_reception_audit(
        action="receipt_issued",
        object_type="receipt",
        object_id=receipt.receipt_code,
        actor=actor,
    )
    return receipt


def ensure_receipt_for_payment(payment: BizPayment, *, actor: str | None = None) -> BizReceipt:
    return issue_receipt_for_payment(payment.id, actor=actor)


def get_receipt(receipt_ref: str) -> dict[str, Any]:
    receipt = _get_receipt(receipt_ref)
    payment = BizPayment.query.get(receipt.payment_id)
    if not payment:
        raise ReceptionWorkspaceError("Payment missing for receipt")
    ctx = _context_payload(payment, receipt)
    return {
        "receipt": receipt.to_dict(include_payloads=True),
        "payment": payment.to_dict(),
        "preview": {
            "html": receipt.html_snapshot or render_receipt_html(ctx),
            "thermal_text": receipt.thermal_payload or render_thermal_payload(ctx),
            "thermal_html": render_receipt_html(ctx, thermal=True),
            "context": ctx,
        },
    }


def list_receipts_for_order(order_ref: str) -> dict[str, Any]:
    order = BizOrder.query.filter(
        or_(BizOrder.order_code == order_ref, BizOrder.id == order_ref)
    ).first()
    if not order:
        raise ReceptionWorkspaceError("Order not found")
    rows = (
        BizReceipt.query.filter_by(order_id=order.id)
        .order_by(BizReceipt.issued_at.desc())
        .all()
    )
    return {
        "order_code": order.order_code,
        "receipts": [r.to_dict() for r in rows],
    }


def preview_receipt(receipt_ref: str, *, format: str = RECEIPT_FORMAT_STANDARD) -> dict[str, Any]:
    data = get_receipt(receipt_ref)
    ctx = data["preview"]["context"]
    thermal = format == RECEIPT_FORMAT_THERMAL
    return {
        "receipt_code": data["receipt"]["receipt_code"],
        "status": data["receipt"]["status"],
        "format": RECEIPT_FORMAT_THERMAL if thermal else RECEIPT_FORMAT_STANDARD,
        "html": render_receipt_html(ctx, thermal=thermal),
        "thermal_text": render_thermal_payload(ctx),
        "context": ctx,
    }


def record_print(
    receipt_ref: str,
    *,
    format: str = RECEIPT_FORMAT_STANDARD,
    actor: str | None = None,
    as_reprint: bool = False,
) -> dict[str, Any]:
    receipt = _get_receipt(receipt_ref)
    if receipt.status == RECEIPT_STATUS_CANCELLED:
        raise ReceptionWorkspaceError("Cannot print a cancelled receipt")
    payment = BizPayment.query.get(receipt.payment_id)
    if not payment:
        raise ReceptionWorkspaceError("Payment missing for receipt")

    receipt.print_count = int(receipt.print_count or 0) + 1
    receipt.last_printed_at = _utcnow_naive()
    receipt.last_printed_by = actor
    if as_reprint or receipt.print_count > 1:
        receipt.status = RECEIPT_STATUS_REPRINTED
    if format in {RECEIPT_FORMAT_STANDARD, RECEIPT_FORMAT_THERMAL}:
        receipt.preferred_format = format
    ctx = _context_payload(payment, receipt)
    ctx["reprint"] = receipt.print_count > 1
    receipt.html_snapshot = render_receipt_html(ctx, thermal=False)
    receipt.thermal_payload = render_thermal_payload(ctx)
    db.session.flush()
    write_reception_audit(
        action="receipt_reprinted" if ctx["reprint"] else "receipt_printed",
        object_type="receipt",
        object_id=receipt.receipt_code,
        actor=actor,
    )
    thermal = format == RECEIPT_FORMAT_THERMAL
    return {
        "receipt": receipt.to_dict(),
        "preview": {
            "html": render_receipt_html(ctx, thermal=thermal),
            "thermal_text": render_thermal_payload(ctx),
            "thermal_html": render_receipt_html(ctx, thermal=True),
            "context": ctx,
        },
    }


def reprint_receipt(
    receipt_ref: str,
    *,
    format: str = RECEIPT_FORMAT_STANDARD,
    actor: str | None = None,
) -> dict[str, Any]:
    return record_print(receipt_ref, format=format, actor=actor, as_reprint=True)


def generate_receipt_pdf(
    receipt_ref: str,
    *,
    actor: str | None = None,
    persist: bool = True,
) -> dict[str, Any]:
    receipt = _get_receipt(receipt_ref)
    if receipt.status == RECEIPT_STATUS_CANCELLED:
        raise ReceptionWorkspaceError("Cannot generate PDF for a cancelled receipt")
    payment = BizPayment.query.get(receipt.payment_id)
    if not payment:
        raise ReceptionWorkspaceError("Payment missing for receipt")
    ctx = _context_payload(payment, receipt)
    ctx["reprint"] = int(receipt.print_count or 0) > 0
    pdf_bytes = build_receipt_pdf_bytes(ctx)
    pdf_path: str | None = None
    if persist:
        path = write_receipt_pdf(ctx, receipt_code=receipt.receipt_code, reprint=int(receipt.print_count or 0))
        receipt.pdf_path = str(path)
        db.session.flush()
        pdf_path = str(path)
    write_reception_audit(
        action="receipt_pdf_generated",
        object_type="receipt",
        object_id=receipt.receipt_code,
        actor=actor,
    )
    return {
        "receipt": receipt.to_dict(),
        "pdf_path": pdf_path,
        "pdf_bytes": pdf_bytes,
        "content_type": "application/pdf",
        "filename": f"{receipt.receipt_code}.pdf",
    }


def cancel_receipt(
    receipt_ref: str,
    *,
    reason: str | None = None,
    actor: str | None = None,
) -> dict[str, Any]:
    receipt = _get_receipt(receipt_ref)
    if receipt.status == RECEIPT_STATUS_CANCELLED:
        return {"receipt": receipt.to_dict(), "idempotent_replay": True}
    receipt.status = RECEIPT_STATUS_CANCELLED
    receipt.cancelled_at = _utcnow_naive()
    receipt.cancelled_by = actor
    receipt.cancel_reason = (reason or "").strip() or "Cancelled at reception desk"
    receipt.updated_at = _utcnow_naive()
    db.session.flush()
    write_reception_audit(
        action="receipt_cancelled",
        object_type="receipt",
        object_id=receipt.receipt_code,
        actor=actor,
    )
    return {"receipt": receipt.to_dict(), "idempotent_replay": False}
