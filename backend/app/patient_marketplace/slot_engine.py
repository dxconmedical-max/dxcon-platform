"""Slot engine — holds, capacity, holidays, working hours, double-booking protection."""

from __future__ import annotations

import json
import secrets
import uuid
from datetime import date, datetime, timedelta
from typing import Any

from app.extensions.db import db
from app.patient_marketplace.constants import QR_EXPIRY_MINUTES, SLOT_HOLD_MINUTES
from app.patient_marketplace.models import MpAvailability, MpHoliday, MpProvider, MpSlotHold
from app.patient_marketplace.service import MarketplaceError


def _utcnow() -> datetime:
    return datetime.utcnow()


def _parse_time(value: str) -> tuple[int, int]:
    parts = value.split(":")
    return int(parts[0]), int(parts[1]) if len(parts) > 1 else 0


class SlotEngineService:
    @staticmethod
    def list_available_slots(
        provider_id: str,
        *,
        organization_id: str,
        slot_date: str,
        duration_minutes: int = 30,
    ) -> dict[str, Any]:
        provider = MpProvider.query.filter_by(id=provider_id, public_status="ACTIVE").first()
        if not provider:
            raise MarketplaceError("Provider not found", 404)
        day = datetime.strptime(slot_date, "%Y-%m-%d").date()
        if SlotEngineService._is_holiday(organization_id, provider_id, day):
            return {"date": slot_date, "slots": [], "reason": "HOLIDAY"}
        windows = SlotEngineService._working_windows(provider, day)
        if not windows:
            return {"date": slot_date, "slots": [], "reason": "CLOSED"}
        slots: list[dict] = []
        for start_h, start_m, end_h, end_m in windows:
            cursor = datetime.combine(day, datetime.min.time()).replace(hour=start_h, minute=start_m)
            end_dt = datetime.combine(day, datetime.min.time()).replace(hour=end_h, minute=end_m)
            while cursor + timedelta(minutes=duration_minutes) <= end_dt:
                slot_end = cursor + timedelta(minutes=duration_minutes)
                avail = MpAvailability.query.filter_by(
                    provider_id=provider_id,
                    organization_id=organization_id,
                    slot_start=cursor,
                ).first()
                capacity = avail.capacity if avail else 1
                reserved = avail.reserved if avail else 0
                blocked = avail.is_blocked if avail else False
                active_holds = MpSlotHold.query.filter_by(
                    provider_id=provider_id,
                    slot_start=cursor,
                    status="HELD",
                ).filter(MpSlotHold.expires_at > _utcnow()).count()
                available = not blocked and reserved + active_holds < capacity
                slots.append({
                    "id": avail.id if avail else f"{provider_id}:{cursor.isoformat()}",
                    "slot_start": cursor.isoformat(),
                    "slot_end": slot_end.isoformat(),
                    "time": cursor.strftime("%H:%M"),
                    "capacity": capacity,
                    "reserved": reserved + active_holds,
                    "available": available,
                })
                cursor += timedelta(minutes=duration_minutes)
        return {"date": slot_date, "slots": slots, "count": len(slots)}

    @staticmethod
    def hold_slot(
        provider_id: str,
        *,
        organization_id: str,
        slot_start: datetime,
        slot_end: datetime,
        patient_user_id: str | None = None,
    ) -> dict:
        SlotEngineService.expire_stale_holds()
        avail = MpAvailability.query.filter_by(
            provider_id=provider_id,
            organization_id=organization_id,
            slot_start=slot_start,
        ).with_for_update().first()
        if not avail:
            avail = MpAvailability(
                organization_id=organization_id,
                provider_id=provider_id,
                slot_start=slot_start,
                slot_end=slot_end,
                capacity=1,
                reserved=0,
            )
            db.session.add(avail)
            db.session.flush()
        if avail.is_blocked:
            raise MarketplaceError("Slot blocked", 409, "SLOT_BLOCKED")
        active_holds = MpSlotHold.query.filter_by(
            provider_id=provider_id,
            slot_start=slot_start,
            status="HELD",
        ).filter(MpSlotHold.expires_at > _utcnow()).count()
        if avail.reserved + active_holds >= avail.capacity:
            raise MarketplaceError("Slot fully booked", 409, "SLOT_FULL")
        token = secrets.token_urlsafe(24)
        expires = _utcnow() + timedelta(minutes=SLOT_HOLD_MINUTES)
        hold = MpSlotHold(
            organization_id=organization_id,
            provider_id=provider_id,
            availability_id=avail.id,
            patient_user_id=patient_user_id,
            hold_token=token,
            slot_start=slot_start,
            slot_end=slot_end,
            expires_at=expires,
        )
        db.session.add(hold)
        db.session.flush()
        return {
            "hold_token": token,
            "expires_at": expires.isoformat(),
            "slot_start": slot_start.isoformat(),
            "slot_end": slot_end.isoformat(),
        }

    @staticmethod
    def confirm_hold(hold_token: str, booking_id: str) -> dict:
        hold = MpSlotHold.query.filter_by(hold_token=hold_token, status="HELD").first()
        if not hold:
            raise MarketplaceError("Hold not found or expired", 404, "HOLD_NOT_FOUND")
        if hold.expires_at < _utcnow():
            hold.status = "EXPIRED"
            raise MarketplaceError("Hold expired", 409, "HOLD_EXPIRED")
        avail = MpAvailability.query.get(hold.availability_id) if hold.availability_id else None
        if avail:
            if avail.reserved >= avail.capacity:
                raise MarketplaceError("Double booking prevented", 409, "SLOT_FULL")
            avail.reserved += 1
        hold.status = "CONFIRMED"
        hold.booking_id = booking_id
        return {"hold_token": hold_token, "status": "CONFIRMED"}

    @staticmethod
    def expire_stale_holds() -> int:
        stale = MpSlotHold.query.filter(
            MpSlotHold.status == "HELD",
            MpSlotHold.expires_at < _utcnow(),
        ).all()
        for hold in stale:
            hold.status = "EXPIRED"
        return len(stale)

    @staticmethod
    def _is_holiday(organization_id: str, provider_id: str, day: date) -> bool:
        row = MpHoliday.query.filter(
            MpHoliday.organization_id == organization_id,
            MpHoliday.holiday_date == day,
            db.or_(MpHoliday.provider_id.is_(None), MpHoliday.provider_id == provider_id),
            MpHoliday.is_closed.is_(True),
        ).first()
        return row is not None

    @staticmethod
    def _working_windows(provider: MpProvider, day: date) -> list[tuple[int, int, int, int]]:
        hours = json.loads(provider.working_hours_json or "{}")
        key = str(day.weekday())
        day_cfg = hours.get(key) or hours.get("default") or {"open": "08:00", "close": "17:00", "closed": False}
        if day_cfg.get("closed"):
            return []
        oh, om = _parse_time(day_cfg.get("open", "08:00"))
        ch, cm = _parse_time(day_cfg.get("close", "17:00"))
        return [(oh, om, ch, cm)]
