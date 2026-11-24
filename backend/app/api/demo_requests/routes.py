"""Public "Book a demo" form on the landing page, plus a staff list.

Public side: one anonymous POST with honeypot, per-IP and global rate limits, strict
validation and a mandatory contact-consent tick. Stores sales-lead contact data only.
Staff side: list under /api/v1/reception (reception-capable login), same as bookings.
"""

from __future__ import annotations

import re
import uuid
from datetime import datetime, timedelta

from flask import Blueprint, request

from app.api.reception_workspace.routes import _client_ip
from app.core.audit import write_audit
from app.extensions.db import db
from app.models.demo_request import DemoRequest
from app.notifications.demo_email import send_demo_notification_async
from app.reception_workspace.auth import reception_api_read

demo_requests_bp = Blueprint("demo_requests", __name__, url_prefix="/api/v1")

PER_IP_PER_HOUR = 5
GLOBAL_PER_DAY = 200
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_PHONE_RE = re.compile(r"^(?:\+?84|0)\d{9,10}$")


def _clean(value, limit: int) -> str:
    return " ".join(str(value or "").split())[:limit]


def _validate(payload: dict):
    lang = "en" if str(payload.get("lang") or "").lower() == "en" else "vi"
    vi = lang == "vi"
    name = _clean(payload.get("full_name"), 120)
    if len(name) < 2:
        return None, "Vui lòng nhập họ tên." if vi else "Please enter your name."
    email = _clean(payload.get("email"), 120)
    if not _EMAIL_RE.match(email):
        return None, "Email chưa đúng." if vi else "Please enter a valid email."
    phone = re.sub(r"[\s.\-()]", "", str(payload.get("phone") or ""))
    if phone and not _PHONE_RE.match(phone):
        return None, "Số điện thoại chưa đúng." if vi else "Please enter a valid phone number."
    message = str(payload.get("message") or "").strip()[:1000]
    if payload.get("consent_contact") is not True:
        return None, ("Vui lòng đồng ý để DxCon liên hệ lại với bạn." if vi
                      else "Please agree to be contacted by DxCon.")
    return {
        "full_name": name, "organization": _clean(payload.get("organization"), 160) or None,
        "email": email, "phone": phone or None, "message": message or None, "lang": lang,
    }, None


def _rate_limited(ip: str) -> bool:
    now = datetime.utcnow()
    if ip:
        recent = DemoRequest.query.filter(
            DemoRequest.ip_address == ip, DemoRequest.created_at >= now - timedelta(hours=1)
        ).count()
        if recent >= PER_IP_PER_HOUR:
            return True
    return DemoRequest.query.filter(DemoRequest.created_at >= now - timedelta(days=1)).count() >= GLOBAL_PER_DAY


@demo_requests_bp.route("/public/demo-requests", methods=["POST"])
def public_demo_create():
    payload = request.get_json(silent=True) or {}
    if str(payload.get("website") or "").strip():  # honeypot
        return {"success": True, "data": {"reference": "DM-RECEIVED"}}, 201
    values, error = _validate(payload)
    if error:
        return {"success": False, "error": error}, 400
    ip = _client_ip()
    if _rate_limited(ip):
        return {"success": False, "error": "Bạn gửi quá nhiều yêu cầu. Vui lòng thử lại sau hoặc gọi 0888 895 151."}, 429
    now = datetime.utcnow()
    row = DemoRequest(
        reference=f"DM-{now:%Y%m%d}-{uuid.uuid4().hex[:6].upper()}",
        consent_contact=True, ip_address=ip, status="NEW", created_at=now, **values,
    )
    db.session.add(row)
    write_audit("PUBLIC_DEMO_REQUEST_CREATED", "DemoRequest", row.reference, ip_address=ip)
    db.session.commit()
    send_demo_notification_async(
        reference=row.reference, full_name=values["full_name"], organization=values["organization"],
        email=values["email"], phone=values["phone"], message=values["message"],
    )
    return {"success": True, "data": {"reference": row.reference}}, 201


@demo_requests_bp.route("/reception/workspace/demo-requests", methods=["GET"])
@reception_api_read
def demo_requests_list():
    rows = DemoRequest.query.order_by(DemoRequest.created_at.desc()).limit(200).all()
    return {"success": True, "data": {"items": [r.to_dict() for r in rows]}}, 200
