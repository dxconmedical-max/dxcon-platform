"""Email that tells a patient their result is ready, with the secure result link.

No test names or values are ever put in the email body: the patient opens the link to see them.
Sent through the same Resend setup as booking emails (RESEND_API_KEY, MAIL_FROM, optional MAIL_REPLY_TO).
"""

from __future__ import annotations

import html
import json
import logging
import os
import urllib.request

from app.notifications.booking_email import RESEND_URL, is_configured

log = logging.getLogger(__name__)


def mask_email(email: str) -> str:
    local, _, domain = email.partition("@")
    return f"{local[:2]}{'*' * max(len(local) - 2, 1)}@{domain}"


def build_result_email(*, full_name: str, order_code: str, url: str, expires_days: int):
    subject = f"DxCon: kết quả xét nghiệm đơn {order_code} đã sẵn sàng"
    text = (
        f"Xin chào {full_name},\n\n"
        f"Kết quả xét nghiệm của bạn (mã đơn {order_code}) đã sẵn sàng.\n"
        f"Xem kết quả tại: {url}\n\n"
        f"Liên kết có hiệu lực {expires_days} ngày. Ai có liên kết này đều xem được kết quả, "
        "vì vậy xin đừng chuyển tiếp cho người khác.\n"
        "Nếu có thắc mắc về kết quả, vui lòng trao đổi với bác sĩ hoặc nơi bạn lấy mẫu.\n\n"
        "DxCon Medical"
    )
    esc = html.escape
    body = (
        '<div style="font-family:Arial,sans-serif;font-size:15px;line-height:1.5;color:#0f172a">'
        f"<p>Xin chào {esc(full_name)},</p>"
        f"<p>Kết quả xét nghiệm của bạn (mã đơn <b>{esc(order_code)}</b>) đã sẵn sàng.</p>"
        f'<p><a href="{esc(url)}" style="display:inline-block;background:#0f766e;color:#fff;padding:10px 18px;'
        'border-radius:8px;text-decoration:none">Xem kết quả</a></p>'
        f'<p style="color:#64748b">Liên kết có hiệu lực {expires_days} ngày. Ai có liên kết này đều xem được kết quả, '
        "vì vậy xin đừng chuyển tiếp cho người khác.</p>"
        "<p>Nếu có thắc mắc về kết quả, vui lòng trao đổi với bác sĩ hoặc nơi bạn lấy mẫu.</p>"
        "<p>DxCon Medical</p></div>"
    )
    return subject, text, body


def send_result_email(*, to: str, full_name: str, order_code: str, url: str, expires_days: int) -> tuple[bool, str]:
    """Returns (ok, reason). Never raises."""
    if not is_configured():
        return False, "not_configured"
    subject, text, body = build_result_email(full_name=full_name, order_code=order_code, url=url, expires_days=expires_days)
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
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:  # noqa: S310 - fixed https URL
            return (200 <= resp.status < 300), "sent"
    except Exception as exc:  # noqa: BLE001
        log.warning("result email failed for %s: %s", order_code, exc)
        return False, "provider_error"
