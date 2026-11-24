"""Internal notification for a new landing-page demo request (best effort, background thread).

Sent through the same Resend setup as booking emails. Recipient: DEMO_NOTIFY_EMAIL,
default support@dxcon.com.vn. The reply-to is the visitor, so staff can just hit Reply.
"""

from __future__ import annotations

import html
import json
import logging
import os
import threading
import urllib.request

from app.notifications.booking_email import RESEND_URL, is_configured

log = logging.getLogger(__name__)
DEFAULT_RECIPIENT = "support@dxcon.com.vn"


def send_demo_notification(*, reference: str, full_name: str, organization: str | None,
                           email: str, phone: str | None, message: str | None) -> bool:
    if not is_configured():
        return False
    esc = html.escape
    to = os.getenv("DEMO_NOTIFY_EMAIL") or DEFAULT_RECIPIENT
    text = (
        f"Yêu cầu demo mới {reference}\n\nHọ tên: {full_name}\nĐơn vị: {organization or '-'}\n"
        f"Email: {email}\nĐiện thoại: {phone or '-'}\n\nNội dung:\n{message or '-'}\n"
    )
    body = (
        '<div style="font-family:Arial,sans-serif;font-size:15px;color:#0f172a">'
        f"<p><b>Yêu cầu demo mới {esc(reference)}</b></p>"
        f"<p>Họ tên: {esc(full_name)}<br>Đơn vị: {esc(organization or '-')}<br>"
        f"Email: {esc(email)}<br>Điện thoại: {esc(phone or '-')}</p>"
        f"<p>Nội dung:<br>{esc(message or '-').replace(chr(10), '<br>')}</p></div>"
    )
    payload = {
        "from": os.environ["MAIL_FROM"], "to": [to], "reply_to": email,
        "subject": f"[DxCon] Yêu cầu demo {reference} - {full_name}", "text": text, "html": body,
    }
    req = urllib.request.Request(
        RESEND_URL, data=json.dumps(payload).encode("utf-8"), method="POST",
        headers={
            "Authorization": f"Bearer {os.environ['RESEND_API_KEY']}",
            "Content-Type": "application/json",
            "User-Agent": "dxcon-platform/1.0",
            "Idempotency-Key": f"demo-{reference}",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:  # noqa: S310 - fixed https URL
            return 200 <= resp.status < 300
    except Exception as exc:  # noqa: BLE001 - never break the request
        log.warning("demo notification failed for %s: %s", reference, exc)
        return False


def send_demo_notification_async(**kwargs) -> None:
    if not is_configured():
        return
    threading.Thread(target=send_demo_notification, kwargs=kwargs, daemon=True).start()
