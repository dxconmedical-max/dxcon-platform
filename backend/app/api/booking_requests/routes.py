"""Public booking requests (website /book) + reception follow-up list.

Public side: one anonymous POST, protected by a honeypot field, per-IP and global
rate limits, strict validation and a mandatory contact-consent tick. It stores
contact and scheduling details only — no health data.

Reception side: list and update status. Lives under /api/v1/reception, so it needs
a reception-capable login like the rest of the workspace.
"""

from __future__ import annotations

import re
import uuid
from datetime import date, datetime, timedelta

from flask import Blueprint, request

from app.api.reception_workspace.routes import _actor, _client_ip
from app.core.audit import write_audit
from app.extensions.db import db
from app.notifications.booking_email import send_booking_confirmation_async
from app.models.booking_request import BookingRequest
from app.reception_workspace.auth import reception_api_read, reception_api_write

booking_requests_bp = Blueprint("booking_requests", __name__, url_prefix="/api/v1")

BOOKING_CONSENT_VERSION = "v1-2026-11"  # lawyer-approved consent text; bump when the text changes
SLOTS = frozenset({"MORNING", "AFTERNOON", "ANYTIME"})
STATUSES = frozenset({"NEW", "CONTACTED", "SCHEDULED", "DONE", "CANCELLED", "SPAM"})
PER_IP_PER_HOUR = 5
GLOBAL_PER_DAY = 300
MAX_DAYS_AHEAD = 60

_PHONE_RE = re.compile(r"^(?:\+?84|0)\d{9,10}$")
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _clean(value, limit: int) -> str:
    return " ".join(str(value or "").split())[:limit]


def _normalize_phone(raw: str) -> str:
    return re.sub(r"[\s.\-()]", "", str(raw or ""))


def _validate(payload: dict) -> tuple[dict | None, str | None]:
    name = _clean(payload.get("full_name"), 120)
    if len(name) < 2:
        return None, "Vui lòng nhập họ tên."
    phone = _normalize_phone(payload.get("phone"))
    if not _PHONE_RE.match(phone):
        return None, "Số điện thoại chưa đúng. Ví dụ: 0901234567."
    address = _clean(payload.get("address"), 300)
    if len(address) < 5:
        return None, "Vui lòng nhập địa chỉ lấy mẫu."
    email = _clean(payload.get("email"), 120)
    if email and not _EMAIL_RE.match(email):
        return None, "Email chưa đúng."
    slot = str(payload.get("preferred_slot") or "ANYTIME").upper()
    if slot not in SLOTS:
        return None, "Khung giờ không hợp lệ."
    preferred = _clean(payload.get("preferred_date"), 10)
    if preferred:
        try:
            chosen = date.fromisoformat(preferred)
        except ValueError:
            return None, "Ngày hẹn không hợp lệ."
        today = date.today()
        if chosen < today or chosen > today + timedelta(days=MAX_DAYS_AHEAD):
            return None, "Ngày hẹn phải từ hôm nay đến 60 ngày tới."
    if payload.get("consent_contact") is not True:
        return None, "Vui lòng đồng ý để DxCon liên hệ lại với bạn."
    return {
        "full_name": name,
        "phone": phone,
        "email": email or None,
        "address": address,
        "district": _clean(payload.get("district"), 100) or None,
        "preferred_date": preferred or None,
        "preferred_slot": slot,
        "note": _clean(payload.get("note"), 500) or None,
    }, None


def _rate_limited(ip: str) -> bool:
    now = datetime.utcnow()
    if ip:
        recent = BookingRequest.query.filter(
            BookingRequest.ip_address == ip,
            BookingRequest.created_at >= now - timedelta(hours=1),
        ).count()
        if recent >= PER_IP_PER_HOUR:
            return True
    today = BookingRequest.query.filter(BookingRequest.created_at >= now - timedelta(days=1)).count()
    return today >= GLOBAL_PER_DAY


@booking_requests_bp.route("/public/bookings", methods=["POST"])
def public_booking_create():
    payload = request.get_json(silent=True) or {}
    # Honeypot: real people never see this field; bots fill it. Pretend success, store nothing.
    if str(payload.get("website") or "").strip():
        return {"success": True, "data": {"reference": "BK-RECEIVED"}}, 201
    values, error = _validate(payload)
    if error:
        return {"success": False, "error": error}, 400
    ip = _client_ip()
    if _rate_limited(ip):
        return {
            "success": False,
            "error": "Bạn gửi quá nhiều yêu cầu. Vui lòng thử lại sau hoặc gọi trực tiếp cho DxCon.",
        }, 429
    now = datetime.utcnow()
    row = BookingRequest(
        reference=f"BK-{now:%Y%m%d}-{uuid.uuid4().hex[:6].upper()}",
        consent_contact=True,
        consent_version=BOOKING_CONSENT_VERSION,
        consent_at=now,
        ip_address=ip,
        status="NEW",
        created_at=now,
        **values,
    )
    db.session.add(row)
    write_audit("PUBLIC_BOOKING_CREATED", "BookingRequest", row.reference, ip_address=ip)
    db.session.commit()
    # Best-effort confirmation email (background thread; never blocks or fails the booking).
    send_booking_confirmation_async(
        to=values.get("email"),
        reference=row.reference,
        full_name=values["full_name"],
        preferred_date=values.get("preferred_date"),
        preferred_slot=values.get("preferred_slot"),
    )
    return {"success": True, "data": {"reference": row.reference}}, 201


@booking_requests_bp.route("/reception/workspace/booking-requests", methods=["GET"])
@reception_api_read
def booking_requests_list():
    status = str(request.args.get("status") or "").upper()
    query = BookingRequest.query
    if status:
        if status not in STATUSES:
            return {"success": False, "error": "Invalid status"}, 400
        query = query.filter(BookingRequest.status == status)
    rows = query.order_by(BookingRequest.created_at.desc()).limit(200).all()
    new_count = BookingRequest.query.filter(BookingRequest.status == "NEW").count()
    return {"success": True, "data": {"items": [r.to_dict() for r in rows], "new_count": new_count}}, 200


@booking_requests_bp.route("/reception/workspace/booking-requests/<request_id>/status", methods=["POST"])
@reception_api_write
def booking_request_set_status(request_id: str):
    payload = request.get_json(silent=True) or {}
    status = str(payload.get("status") or "").upper()
    if status not in STATUSES:
        return {"success": False, "error": "Invalid status"}, 400
    row = db.session.get(BookingRequest, request_id)
    if row is None:
        return {"success": False, "error": "Booking request not found"}, 404
    actor = _actor()
    row.status = status
    row.handled_by = (actor or "")[:120] or None
    row.handled_at = datetime.utcnow()
    note = _clean(payload.get("internal_note"), 500)
    if note:
        row.internal_note = note
    write_audit("PUBLIC_BOOKING_STATUS", "BookingRequest", row.reference, user_email=actor or "SYSTEM", ip_address=_client_ip())
    db.session.commit()
    return {"success": True, "data": row.to_dict()}, 200
