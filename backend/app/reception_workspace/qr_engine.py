"""Reception QR Engine — payment, VNPay, static/dynamic, sample, tracking.

Payload scheme (prefix ``dxcon:``):
  patient / order / sample / pay / vnpay / track / dyn
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import io
import os
import time
import uuid
from datetime import datetime
from typing import Any
from urllib.parse import quote, urlencode

from app.models.biz_order import BizOrder
from app.reception_workspace.audit import write_reception_audit
from app.reception_workspace.errors import ReceptionWorkspaceError

# --- kinds -----------------------------------------------------------------

QR_PAYMENT = "payment"
QR_VNPAY = "vnpay"
QR_STATIC = "static"
QR_DYNAMIC = "dynamic"
QR_SAMPLE = "sample"
QR_TRACKING = "tracking"

QR_KINDS = (
    QR_PAYMENT,
    QR_VNPAY,
    QR_STATIC,
    QR_DYNAMIC,
    QR_SAMPLE,
    QR_TRACKING,
)

PREFIX_PATIENT = "dxcon:patient:"
PREFIX_ORDER = "dxcon:order:"
PREFIX_SAMPLE = "dxcon:sample:"
PREFIX_PAY = "dxcon:pay:"
PREFIX_VNPAY = "dxcon:vnpay:"
PREFIX_TRACK = "dxcon:track:"
PREFIX_DYN = "dxcon:dyn:"

DEFAULT_DYNAMIC_TTL_SEC = 15 * 60


def list_qr_kinds() -> list[dict[str, str]]:
    return [
        {"id": QR_PAYMENT, "label": "Payment QR", "prefix": PREFIX_PAY},
        {"id": QR_VNPAY, "label": "VNPay QR", "prefix": PREFIX_VNPAY},
        {"id": QR_STATIC, "label": "Static QR", "prefix": f"{PREFIX_PATIENT}|{PREFIX_ORDER}"},
        {"id": QR_DYNAMIC, "label": "Dynamic QR", "prefix": PREFIX_DYN},
        {"id": QR_SAMPLE, "label": "Sample QR", "prefix": PREFIX_SAMPLE},
        {"id": QR_TRACKING, "label": "Tracking QR", "prefix": PREFIX_TRACK},
    ]


def _qr_secret() -> str:
    try:
        from flask import current_app, has_app_context

        if has_app_context():
            cfg = current_app.config.get("DXCON_QR_SECRET") or current_app.config.get("SECRET_KEY")
            if cfg:
                return str(cfg)
    except Exception:
        pass
    return os.getenv("DXCON_QR_SECRET") or os.getenv("SECRET_KEY") or "dxcon-dev-qr-secret"


def _public_base() -> str:
    try:
        from flask import current_app, has_app_context, has_request_context, request

        if has_app_context():
            base = (current_app.config.get("PUBLIC_BASE_URL") or "").rstrip("/")
            if base:
                return base
        if has_request_context():
            return request.url_root.rstrip("/")
    except Exception:
        pass
    return (os.getenv("PUBLIC_BASE_URL") or "").rstrip("/")


def _sign(parts: list[str]) -> str:
    msg = "|".join(parts).encode("utf-8")
    return hmac.new(_qr_secret().encode("utf-8"), msg, hashlib.sha256).hexdigest()[:24]


def render_qr_png_data_url(payload: str) -> str:
    """Encode payload as PNG QR data URL (requires ``qrcode`` + Pillow)."""
    import qrcode

    qr = qrcode.QRCode(version=None, box_size=4, border=2, error_correction=qrcode.constants.ERROR_CORRECT_M)
    qr.add_data(payload)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode("ascii")
    return f"data:image/png;base64,{b64}"


def _card(
    *,
    kind: str,
    title: str,
    payload: str,
    static: bool,
    meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "kind": kind,
        "title": title,
        "payload": payload,
        "static": static,
        "image_data_url": render_qr_png_data_url(payload),
        "meta": meta or {},
    }


def _resolve_order(order_ref: str) -> BizOrder:
    from sqlalchemy import or_

    order = BizOrder.query.filter(
        or_(BizOrder.order_code == order_ref, BizOrder.id == order_ref)
    ).first()
    if not order:
        raise ReceptionWorkspaceError("Order not found")
    return order


def _payment_amount(order: BizOrder, amount: float | None = None) -> float:
    from app.reception_workspace.payment_engine import build_payment_summary

    summary = build_payment_summary(order)
    outstanding = float(summary.get("outstanding_amount") or 0)
    if amount is not None:
        pay = round(float(amount), 2)
        if pay <= 0:
            raise ReceptionWorkspaceError("Payment QR amount must be greater than zero")
        return pay
    if outstanding > 0:
        return outstanding
    # Fully paid — still allow a settled payment QR for the order total (reprint / archive)
    total = float(summary.get("order_total") or order.total_amount or 0)
    if total <= 0:
        raise ReceptionWorkspaceError("Order has no payable amount for payment QR")
    return total


def build_payment_qr(order: BizOrder, *, amount: float | None = None) -> dict[str, Any]:
    pay_amount = _payment_amount(order, amount)
    currency = "VND"
    # amount stored as integer đồng for stable encoding
    amount_int = int(round(pay_amount))
    payload = f"{PREFIX_PAY}{order.order_code}:{amount_int}:{currency}"
    return _card(
        kind=QR_PAYMENT,
        title="Payment QR",
        payload=payload,
        static=False,
        meta={
            "order_code": order.order_code,
            "amount": pay_amount,
            "currency": currency,
            "method_hint": "qr",
        },
    )


def build_vnpay_qr(order: BizOrder, *, amount: float | None = None) -> dict[str, Any]:
    """VNPay / Viet-style payment QR (sandbox-friendly; signs when secret set)."""
    pay_amount = _payment_amount(order, amount)
    amount_x100 = int(round(pay_amount * 100))
    txn_ref = f"VNP{datetime.utcnow().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:6].upper()}"
    tmn = os.getenv("VNPAY_TMN_CODE", "DXCONDEMO")
    create_date = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    order_info = f"DxCon {order.order_code}"
    params = {
        "vnp_Version": "2.1.0",
        "vnp_Command": "pay",
        "vnp_TmnCode": tmn,
        "vnp_Amount": str(amount_x100),
        "vnp_CurrCode": "VND",
        "vnp_TxnRef": txn_ref,
        "vnp_OrderInfo": order_info,
        "vnp_OrderType": "billpayment",
        "vnp_Locale": "vn",
        "vnp_CreateDate": create_date,
        "vnp_IpAddr": "127.0.0.1",
    }
    # Compact signed internal payload for offline verify + image
    sig = _sign([txn_ref, str(amount_x100), order.order_code, tmn])
    compact = f"{PREFIX_VNPAY}{txn_ref}:{amount_x100}:{order.order_code}:{sig}"

    hash_secret = os.getenv("VNPAY_HASH_SECRET", "")
    query = urlencode(sorted(params.items()))
    if hash_secret:
        secure = hmac.new(
            hash_secret.encode("utf-8"),
            query.encode("utf-8"),
            hashlib.sha512,
        ).hexdigest()
        payment_url = (
            f"https://sandbox.vnpayment.vn/paymentv2/vpcpay.html?{query}&vnp_SecureHash={secure}"
        )
    else:
        payment_url = f"https://sandbox.vnpayment.vn/paymentv2/vpcpay.html?{query}"

    card = _card(
        kind=QR_VNPAY,
        title="VNPay QR",
        payload=compact,
        static=False,
        meta={
            "order_code": order.order_code,
            "amount": pay_amount,
            "amount_x100": amount_x100,
            "currency": "VND",
            "txn_ref": txn_ref,
            "tmn_code": tmn,
            "payment_url": payment_url,
            "provider": "VNPAY",
            "sandbox": True,
        },
    )
    # Prefer scanning the payment URL when a gateway secret is configured
    if hash_secret:
        card["payload"] = payment_url
        card["meta"]["compact_payload"] = compact
        card["image_data_url"] = render_qr_png_data_url(payment_url)
    return card


def build_static_qrs(order: BizOrder) -> list[dict[str, Any]]:
    cards = [
        _card(
            kind=QR_STATIC,
            title="Patient (static)",
            payload=f"{PREFIX_PATIENT}{order.patient_code}",
            static=True,
            meta={"patient_code": order.patient_code, "subtype": "patient"},
        ),
        _card(
            kind=QR_STATIC,
            title="Order (static)",
            payload=f"{PREFIX_ORDER}{order.order_code}",
            static=True,
            meta={"order_code": order.order_code, "subtype": "order"},
        ),
    ]
    return cards


def build_dynamic_qr(
    order: BizOrder,
    *,
    purpose: str = "handoff",
    ttl_sec: int = DEFAULT_DYNAMIC_TTL_SEC,
) -> dict[str, Any]:
    purpose = (purpose or "handoff").strip().lower() or "handoff"
    nonce = uuid.uuid4().hex[:10]
    exp = int(time.time()) + max(60, int(ttl_sec))
    sig = _sign([purpose, order.order_code, nonce, str(exp)])
    payload = f"{PREFIX_DYN}{purpose}:{order.order_code}:{nonce}:{exp}:{sig}"
    return _card(
        kind=QR_DYNAMIC,
        title="Dynamic QR",
        payload=payload,
        static=False,
        meta={
            "order_code": order.order_code,
            "purpose": purpose,
            "expires_at": datetime.utcfromtimestamp(exp).isoformat() + "Z",
            "ttl_sec": ttl_sec,
        },
    )


def build_sample_qrs(order: BizOrder) -> list[dict[str, Any]]:
    from app.reception_workspace.service import generate_barcodes

    barcodes = generate_barcodes(order.order_code)
    cards = []
    for sample in barcodes.get("sample_barcodes") or []:
        specimen = sample.get("specimen_code") or sample.get("barcode")
        if not specimen:
            continue
        payload = f"{PREFIX_SAMPLE}{specimen}"
        cards.append(
            _card(
                kind=QR_SAMPLE,
                title=f"Sample {sample.get('test_code') or ''}".strip(),
                payload=payload,
                static=True,
                meta={
                    "specimen_code": specimen,
                    "barcode": sample.get("barcode"),
                    "test_code": sample.get("test_code"),
                    "test_name": sample.get("test_name"),
                },
            )
        )
    return cards


def build_tracking_qr(order: BizOrder) -> dict[str, Any]:
    payload = f"{PREFIX_TRACK}{order.order_code}"
    base = _public_base()
    track_path = f"/track/{quote(order.order_code, safe='')}"
    track_url = f"{base}{track_path}" if base else track_path
    return _card(
        kind=QR_TRACKING,
        title="Tracking QR",
        payload=payload,
        static=True,
        meta={
            "order_code": order.order_code,
            "track_url": track_url,
            "status": order.status,
        },
    )


def build_qr_bundle(
    order_ref: str,
    *,
    kinds: list[str] | None = None,
    amount: float | None = None,
    dynamic_ttl_sec: int = DEFAULT_DYNAMIC_TTL_SEC,
    include_images: bool = True,
) -> dict[str, Any]:
    order = _resolve_order(order_ref)
    wanted = {k.strip().lower() for k in (kinds or list(QR_KINDS)) if k}
    if not wanted:
        wanted = set(QR_KINDS)

    qrs: list[dict[str, Any]] = []

    if QR_PAYMENT in wanted:
        qrs.append(build_payment_qr(order, amount=amount))
    if QR_VNPAY in wanted:
        qrs.append(build_vnpay_qr(order, amount=amount))
    if QR_STATIC in wanted:
        qrs.extend(build_static_qrs(order))
    if QR_DYNAMIC in wanted:
        qrs.append(build_dynamic_qr(order, ttl_sec=dynamic_ttl_sec))
    if QR_SAMPLE in wanted:
        try:
            qrs.extend(build_sample_qrs(order))
        except ReceptionWorkspaceError as exc:
            qrs.append(
                {
                    "kind": QR_SAMPLE,
                    "title": "Sample QR",
                    "payload": None,
                    "static": True,
                    "image_data_url": None,
                    "unavailable": True,
                    "meta": {"reason": str(exc)},
                }
            )
    if QR_TRACKING in wanted:
        qrs.append(build_tracking_qr(order))

    if not include_images:
        for card in qrs:
            card.pop("image_data_url", None)

    write_reception_audit(
        action="qr_bundle_generated",
        object_type="order",
        object_id=order.order_code,
    )
    return {
        "order_code": order.order_code,
        "patient_code": order.patient_code,
        "patient_name": order.patient_name,
        "status": order.status,
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "kinds": sorted(wanted),
        "qrs": qrs,
        "kind_catalog": list_qr_kinds(),
    }


def preview_qr_html(bundle: dict[str, Any]) -> str:
    cards = []
    for qr in bundle.get("qrs") or []:
        if qr.get("unavailable") or not qr.get("payload"):
            body = f"<div class='muted'>{_esc(qr.get('meta', {}).get('reason') or 'Unavailable')}</div>"
        else:
            img = ""
            if qr.get("image_data_url"):
                img = f"<img alt='qr' src='{_esc(qr['image_data_url'])}'/>"
            body = (
                f"<div class='title'>{_esc(qr.get('title'))}</div>"
                f"{img}"
                f"<div class='payload'>{_esc(qr.get('payload'))}</div>"
            )
        cards.append(f"<div class='card'>{body}</div>")
    return f"""<!doctype html>
<html><head><meta charset="utf-8"/><title>DxCon QR</title>
<style>
body {{ font-family: ui-sans-serif, system-ui, sans-serif; margin: 12px; }}
.card {{ border: 1px solid #cbd5e1; padding: 12px; margin: 0 0 12px; page-break-inside: avoid; }}
.title {{ font-weight: 700; margin-bottom: 8px; }}
.payload {{ font-family: ui-monospace, Menlo, monospace; font-size: 11px; word-break: break-all; margin-top: 8px; }}
img {{ width: 160px; height: 160px; }}
.muted {{ color: #64748b; }}
</style></head><body>
<h1>QR pack — {_esc(bundle.get('order_code'))}</h1>
{''.join(cards)}
</body></html>"""


def _esc(value: Any) -> str:
    text = "" if value is None else str(value)
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def verify_qr_payload(payload: str, *, order_ref: str | None = None) -> dict[str, Any]:
    """Verify format, signature (dynamic/VNPay compact), and optional order binding."""
    raw = (payload or "").strip()
    if not raw:
        raise ReceptionWorkspaceError("QR payload is required")

    result: dict[str, Any] = {
        "payload": raw,
        "valid": False,
        "kind": None,
        "reason": None,
        "fields": {},
    }

    def ok(kind: str, fields: dict[str, Any], *, reason: str = "ok") -> dict[str, Any]:
        result.update(valid=True, kind=kind, reason=reason, fields=fields)
        return result

    def bad(kind: str | None, reason: str, fields: dict[str, Any] | None = None) -> dict[str, Any]:
        result.update(valid=False, kind=kind, reason=reason, fields=fields or {})
        return result

    if raw.startswith(PREFIX_PATIENT):
        code = raw[len(PREFIX_PATIENT) :]
        if not code:
            return bad(QR_STATIC, "Empty patient code")
        if order_ref:
            order = _resolve_order(order_ref)
            if order.patient_code != code:
                return bad(QR_STATIC, "Patient code does not match order", {"patient_code": code})
        return ok(QR_STATIC, {"subtype": "patient", "patient_code": code})

    if raw.startswith(PREFIX_ORDER):
        code = raw[len(PREFIX_ORDER) :]
        if not code:
            return bad(QR_STATIC, "Empty order code")
        if order_ref and _resolve_order(order_ref).order_code != code:
            return bad(QR_STATIC, "Order code mismatch", {"order_code": code})
        return ok(QR_STATIC, {"subtype": "order", "order_code": code})

    if raw.startswith(PREFIX_SAMPLE):
        specimen = raw[len(PREFIX_SAMPLE) :]
        if not specimen:
            return bad(QR_SAMPLE, "Empty specimen code")
        return ok(QR_SAMPLE, {"specimen_code": specimen})

    if raw.startswith(PREFIX_PAY):
        body = raw[len(PREFIX_PAY) :]
        parts = body.split(":")
        if len(parts) < 3:
            return bad(QR_PAYMENT, "Malformed payment QR")
        order_code, amount_s, currency = parts[0], parts[1], parts[2]
        try:
            amount = int(amount_s)
        except ValueError:
            return bad(QR_PAYMENT, "Invalid payment amount")
        if order_ref and _resolve_order(order_ref).order_code != order_code:
            return bad(QR_PAYMENT, "Payment QR order mismatch", {"order_code": order_code})
        return ok(
            QR_PAYMENT,
            {"order_code": order_code, "amount": amount, "currency": currency},
        )

    if raw.startswith(PREFIX_VNPAY):
        body = raw[len(PREFIX_VNPAY) :]
        parts = body.split(":")
        if len(parts) < 4:
            return bad(QR_VNPAY, "Malformed VNPay QR")
        txn_ref, amount_s, order_code, sig = parts[0], parts[1], parts[2], parts[3]
        expected = _sign([txn_ref, amount_s, order_code, os.getenv("VNPAY_TMN_CODE", "DXCONDEMO")])
        if not hmac.compare_digest(sig, expected):
            return bad(QR_VNPAY, "Invalid VNPay QR signature")
        if order_ref and _resolve_order(order_ref).order_code != order_code:
            return bad(QR_VNPAY, "VNPay QR order mismatch")
        return ok(
            QR_VNPAY,
            {
                "txn_ref": txn_ref,
                "amount_x100": int(amount_s),
                "order_code": order_code,
            },
        )

    if raw.startswith("https://") and "vnpayment.vn" in raw:
        return ok(QR_VNPAY, {"payment_url": raw, "subtype": "vnpay_url"})

    if raw.startswith(PREFIX_TRACK):
        code = raw[len(PREFIX_TRACK) :]
        if not code:
            return bad(QR_TRACKING, "Empty tracking order code")
        if order_ref and _resolve_order(order_ref).order_code != code:
            return bad(QR_TRACKING, "Tracking order mismatch")
        return ok(QR_TRACKING, {"order_code": code})

    if raw.startswith(PREFIX_DYN):
        body = raw[len(PREFIX_DYN) :]
        parts = body.split(":")
        if len(parts) != 5:
            return bad(QR_DYNAMIC, "Malformed dynamic QR")
        purpose, order_code, nonce, exp_s, sig = parts
        try:
            exp = int(exp_s)
        except ValueError:
            return bad(QR_DYNAMIC, "Invalid expiry")
        expected = _sign([purpose, order_code, nonce, exp_s])
        if not hmac.compare_digest(sig, expected):
            return bad(QR_DYNAMIC, "Invalid dynamic QR signature")
        if int(time.time()) > exp:
            return bad(
                QR_DYNAMIC,
                "Dynamic QR expired",
                {"order_code": order_code, "purpose": purpose, "expires_at": exp},
            )
        if order_ref and _resolve_order(order_ref).order_code != order_code:
            return bad(QR_DYNAMIC, "Dynamic QR order mismatch")
        return ok(
            QR_DYNAMIC,
            {
                "purpose": purpose,
                "order_code": order_code,
                "nonce": nonce,
                "expires_at": datetime.utcfromtimestamp(exp).isoformat() + "Z",
            },
        )

    return bad(None, "Unrecognized QR payload scheme")
