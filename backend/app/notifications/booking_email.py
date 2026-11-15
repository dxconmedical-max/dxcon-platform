"""Booking confirmation email, sent through the Resend HTTP API.

Content is deliberately minimal: booking code, name, preferred date and slot.
No phone, address, note or any health information is ever put in the email.

Configuration (environment, set in Coolify):
  RESEND_API_KEY   Resend API key (Sending access)
  MAIL_FROM        e.g. "DxCon <no-reply@dxcon.com.vn>"
  MAIL_REPLY_TO    optional reply-to address

Sending is best-effort and runs in a background thread: a mail problem must
never make a booking fail or slow down.
"""

from __future__ import annotations

import html
import json
import logging
import os
import threading
import urllib.request
from datetime import date

log = logging.getLogger(__name__)

RESEND_URL = "https://api.resend.com/emails"
SLOT_LABELS = {
    "MORNING": "Buổi sáng",
    "AFTERNOON": "Buổi chiều",
    "ANYTIME": "Linh hoạt trong ngày",
}


def is_configured() -> bool:
    return bool(os.getenv("RESEND_API_KEY") and os.getenv("MAIL_FROM"))


def _date_label(value: str | None) -> str:
    if not value:
        return "Chưa chọn ngày (DxCon sẽ liên hệ để sắp xếp)"
    try:
        return date.fromisoformat(value).strftime("%d/%m/%Y")
    except ValueError:
        return "Chưa chọn ngày (DxCon sẽ liên hệ để sắp xếp)"


def build_booking_email(*, reference: str, full_name: str, preferred_date: str | None, preferred_slot: str | None):
    slot = SLOT_LABELS.get(str(preferred_slot or "ANYTIME").upper(), SLOT_LABELS["ANYTIME"])
    when = _date_label(preferred_date)
    subject = f"DxCon đã nhận yêu cầu đặt lịch {reference}"
    text = (
        f"Xin chào {full_name},\n\n"
        "DxCon đã nhận được yêu cầu đặt lịch lấy mẫu của bạn.\n\n"
        f"Mã đặt lịch: {reference}\n"
        f"Ngày mong muốn: {when}\n"
        f"Khung giờ: {slot}\n\n"
        "Nhân viên DxCon sẽ liên hệ để xác nhận lịch hẹn. "
        "Email này chỉ xác nhận đã nhận yêu cầu, chưa phải xác nhận lịch hẹn cuối cùng.\n\n"
        "Nếu bạn không gửi yêu cầu này, vui lòng bỏ qua email.\n\n"
        "DxCon Medical"
    )
    esc = html.escape
    body = (
        '<div style="font-family:Arial,sans-serif;font-size:15px;line-height:1.5;color:#0f172a">'
        f"<p>Xin chào {esc(full_name)},</p>"
        "<p>DxCon đã nhận được yêu cầu đặt lịch lấy mẫu của bạn.</p>"
        "<table cellpadding=\"4\" style=\"border-collapse:collapse\">"
        f"<tr><td><b>Mã đặt lịch</b></td><td>{esc(reference)}</td></tr>"
        f"<tr><td><b>Ngày mong muốn</b></td><td>{esc(when)}</td></tr>"
        f"<tr><td><b>Khung giờ</b></td><td>{esc(slot)}</td></tr>"
        "</table>"
        "<p>Nhân viên DxCon sẽ liên hệ để xác nhận lịch hẹn. Email này chỉ xác nhận đã nhận yêu cầu, "
        "chưa phải xác nhận lịch hẹn cuối cùng.</p>"
        '<p style="color:#64748b">Nếu bạn không gửi yêu cầu này, vui lòng bỏ qua email.</p>'
        "<p>DxCon Medical</p></div>"
    )
    return subject, text, body


def send_booking_confirmation(
    *, to: str, reference: str, full_name: str, preferred_date: str | None, preferred_slot: str | None
) -> bool:
    """Send synchronously. Returns True on success, False otherwise (never raises)."""
    if not to or not is_configured():
        return False
    subject, text, body = build_booking_email(
        reference=reference, full_name=full_name, preferred_date=preferred_date, preferred_slot=preferred_slot
    )
    payload = {"from": os.environ["MAIL_FROM"], "to": [to], "subject": subject, "text": text, "html": body}
    reply_to = os.getenv("MAIL_REPLY_TO")
    if reply_to:
        payload["reply_to"] = reply_to
    req = urllib.request.Request(
        RESEND_URL,
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={
            "Authorization": f"Bearer {os.environ['RESEND_API_KEY']}",
            "Content-Type": "application/json",
            "User-Agent": "dxcon-platform/1.0",
            "Idempotency-Key": f"booking-{reference}",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:  # noqa: S310 - fixed https URL
            return 200 <= resp.status < 300
    except Exception as exc:  # noqa: BLE001 - best effort, never break a booking
        log.warning("booking confirmation email failed for %s: %s", reference, exc)
        return False


def send_booking_confirmation_async(**kwargs) -> None:
    if not kwargs.get("to") or not is_configured():
        return
    threading.Thread(target=send_booking_confirmation, kwargs=kwargs, daemon=True).start()
