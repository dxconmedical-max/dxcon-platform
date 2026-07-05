"""Reception Center business logic for Sprint 2.1."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from sqlalchemy import func, or_

from app.core.audit import write_audit
from app.extensions.db import db
from app.infrastructure.schema_introspection import table_exists_name
from app.models.clinic_booking import ClinicBooking
from app.models.patient import Patient
from app.models.reception_activity_log import ReceptionActivityLog
from app.models.reception_queue_entry import ReceptionQueueEntry


class ReceptionError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


RECEPTION_ROLES = ("SUPER_ADMIN", "ADMIN", "RECEPTION")
VISIT_WALK_IN = "WALK_IN"
VISIT_APPOINTMENT = "APPOINTMENT"
VISIT_QUICK_REG = "QUICK_REG"
STATUS_WAITING = "WAITING"
STATUS_CHECKED_IN = "CHECKED_IN"
STATUS_CHECKED_OUT = "CHECKED_OUT"


def _today() -> date:
    return date.today()


def _actor_email(actor: str | None) -> str:
    return actor or "SYSTEM"


def log_activity(
    action: str,
    *,
    patient_id: str | None = None,
    queue_entry_id: str | None = None,
    details: str | None = None,
    actor_email: str | None = None,
) -> ReceptionActivityLog | None:
    if not table_exists_name("reception_activity_logs"):
        return None
    entry = ReceptionActivityLog(
        action=action,
        patient_id=patient_id,
        queue_entry_id=queue_entry_id,
        details=details,
        actor_email=_actor_email(actor_email),
    )
    db.session.add(entry)
    return entry


def next_queue_number(queue_day: date | None = None) -> tuple[str, int]:
    queue_day = queue_day or _today()
    if not table_exists_name("reception_queue_entries"):
        return f"Q{queue_day.strftime('%Y%m%d')}-001", 1
    last_seq = (
        db.session.query(func.max(ReceptionQueueEntry.daily_sequence))
        .filter(ReceptionQueueEntry.queue_date == queue_day)
        .scalar()
    ) or 0
    sequence = int(last_seq) + 1
    number = f"Q{queue_day.strftime('%Y%m%d')}-{sequence:03d}"
    return number, sequence


def next_patient_code(prefix: str = "RC") -> str:
    today = _today()
    pattern = f"{prefix}-{today.strftime('%Y%m%d')}-%"
    count = Patient.query.filter(Patient.patient_code.like(pattern)).count()
    return f"{prefix}-{today.strftime('%Y%m%d')}-{(count + 1):04d}"


def search_patients(
    *,
    code: str | None = None,
    phone: str | None = None,
    national_id: str | None = None,
    name: str | None = None,
    limit: int = 25,
) -> list[Patient]:
    query = Patient.query
    if code:
        query = query.filter(Patient.patient_code.ilike(f"%{code.strip()}%"))
    if phone:
        query = query.filter(Patient.phone.ilike(f"%{phone.strip()}%"))
    if national_id:
        query = query.filter(Patient.national_id.ilike(f"%{national_id.strip()}%"))
    if name:
        query = query.filter(Patient.full_name.ilike(f"%{name.strip()}%"))
    return query.order_by(Patient.full_name).limit(limit).all()


def register_patient_quick(
    *,
    full_name: str,
    phone: str,
    gender: str | None = None,
    actor_email: str | None = None,
) -> tuple[Patient, ReceptionQueueEntry]:
    if not full_name or not phone:
        raise ReceptionError("Full name and phone are required")
    existing = Patient.query.filter_by(phone=phone.strip()).first()
    if existing:
        raise ReceptionError(f"Patient already exists with phone {phone}", 409)
    patient = Patient(
        patient_code=next_patient_code("RC"),
        full_name=full_name.strip(),
        phone=phone.strip(),
        gender=gender,
    )
    db.session.add(patient)
    db.session.flush()
    queue_entry = create_queue_entry(
        patient.patient_code,
        visit_type=VISIT_QUICK_REG,
        actor_email=actor_email,
    )
    write_audit("QUICK_REGISTER", "PATIENT", patient.patient_code, user_email=_actor_email(actor_email))
    log_activity(
        "QUICK_REGISTER",
        patient_id=patient.patient_code,
        queue_entry_id=queue_entry.id,
        details=f"Quick registration for {patient.full_name}",
        actor_email=actor_email,
    )
    patient_code = patient.patient_code
    queue_number = queue_entry.queue_number
    db.session.commit()
    return {"patient_code": patient_code, "queue_number": queue_number}


def register_walk_in(
    *,
    full_name: str,
    phone: str,
    national_id: str | None = None,
    gender: str | None = None,
    address: str | None = None,
    actor_email: str | None = None,
) -> tuple[Patient, ReceptionQueueEntry]:
    if not full_name or not phone:
        raise ReceptionError("Full name and phone are required")
    patient = Patient.query.filter_by(phone=phone.strip()).first()
    created = False
    if not patient:
        patient = Patient(
            patient_code=next_patient_code("WI"),
            full_name=full_name.strip(),
            phone=phone.strip(),
            national_id=national_id,
            gender=gender,
            address=address,
        )
        db.session.add(patient)
        db.session.flush()
        created = True
        write_audit("WALK_IN_REGISTER", "PATIENT", patient.patient_code, user_email=_actor_email(actor_email))
    queue_entry = create_queue_entry(
        patient.patient_code,
        visit_type=VISIT_WALK_IN,
        actor_email=actor_email,
        notes="New patient walk-in" if created else "Existing patient walk-in",
    )
    log_activity(
        "WALK_IN",
        patient_id=patient.patient_code,
        queue_entry_id=queue_entry.id,
        details=queue_entry.notes,
        actor_email=actor_email,
    )
    patient_code = patient.patient_code
    queue_number = queue_entry.queue_number
    db.session.commit()
    return {"patient_code": patient_code, "queue_number": queue_number}


def create_queue_entry(
    patient_id: str,
    *,
    visit_type: str = VISIT_WALK_IN,
    appointment_id: str | None = None,
    payment_status: str = "PENDING",
    notes: str | None = None,
    actor_email: str | None = None,
) -> ReceptionQueueEntry:
    if not table_exists_name("reception_queue_entries"):
        raise ReceptionError("Reception queue table is not available", 503)
    patient = Patient.query.get(patient_id)
    if not patient:
        raise ReceptionError("Patient not found", 404)
    queue_day = _today()
    queue_number, sequence = next_queue_number(queue_day)
    entry = ReceptionQueueEntry(
        queue_number=queue_number,
        queue_date=queue_day,
        daily_sequence=sequence,
        patient_id=patient_id,
        visit_type=visit_type,
        status=STATUS_WAITING,
        appointment_id=appointment_id,
        payment_status=payment_status,
        notes=notes,
        created_by=_actor_email(actor_email),
    )
    db.session.add(entry)
    log_activity(
        "QUEUE_ISSUED",
        patient_id=patient_id,
        queue_entry_id=entry.id,
        details=f"Queue {queue_number} ({visit_type})",
        actor_email=actor_email,
    )
    return entry


def check_in_appointment(
    *,
    booking_code: str | None = None,
    patient_id: str | None = None,
    actor_email: str | None = None,
) -> tuple[ClinicBooking, ReceptionQueueEntry]:
    if not booking_code and not patient_id:
        raise ReceptionError("Booking code or patient ID is required")
    booking = None
    if booking_code:
        booking = ClinicBooking.query.filter_by(booking_code=booking_code.strip()).first()
    elif patient_id:
        booking = (
            ClinicBooking.query.filter_by(patient_id=patient_id.strip())
            .filter(ClinicBooking.status.in_(("PENDING", "CONFIRMED", "SCHEDULED")))
            .order_by(ClinicBooking.scheduled_at.asc())
            .first()
        )
    if not booking:
        raise ReceptionError("Appointment not found", 404)
    booking.status = "CHECKED_IN"
    queue_entry = create_queue_entry(
        booking.patient_id,
        visit_type=VISIT_APPOINTMENT,
        appointment_id=booking.id,
        notes=f"Appointment {booking.booking_code}",
        actor_email=actor_email,
    )
    queue_entry.status = STATUS_CHECKED_IN
    queue_entry.checked_in_at = datetime.utcnow()
    log_activity(
        "APPOINTMENT_CHECK_IN",
        patient_id=booking.patient_id,
        queue_entry_id=queue_entry.id,
        details=f"Booking {booking.booking_code}",
        actor_email=actor_email,
    )
    write_audit("APPOINTMENT_CHECK_IN", "CLINIC_BOOKING", booking.id, user_email=_actor_email(actor_email))
    booking_code = booking.booking_code
    queue_number = queue_entry.queue_number
    patient_code = booking.patient_id
    db.session.commit()
    return {
        "booking_code": booking_code,
        "patient_code": patient_code,
        "queue_number": queue_number,
    }


def check_in_queue(entry_id: str, *, actor_email: str | None = None) -> ReceptionQueueEntry:
    entry = ReceptionQueueEntry.query.get(entry_id)
    if not entry:
        raise ReceptionError("Queue entry not found", 404)
    if entry.status == STATUS_CHECKED_OUT:
        raise ReceptionError("Patient already checked out")
    entry.status = STATUS_CHECKED_IN
    entry.checked_in_at = datetime.utcnow()
    log_activity(
        "CHECK_IN",
        patient_id=entry.patient_id,
        queue_entry_id=entry.id,
        details=f"Queue {entry.queue_number}",
        actor_email=actor_email,
    )
    db.session.commit()
    return entry


def check_out_queue(entry_id: str, *, actor_email: str | None = None) -> ReceptionQueueEntry:
    entry = ReceptionQueueEntry.query.get(entry_id)
    if not entry:
        raise ReceptionError("Queue entry not found", 404)
    entry.status = STATUS_CHECKED_OUT
    entry.checked_out_at = datetime.utcnow()
    log_activity(
        "CHECK_OUT",
        patient_id=entry.patient_id,
        queue_entry_id=entry.id,
        details=f"Queue {entry.queue_number}",
        actor_email=actor_email,
    )
    db.session.commit()
    return entry


def today_queue_entries(*, status: str | None = None) -> list[ReceptionQueueEntry]:
    if not table_exists_name("reception_queue_entries"):
        return []
    query = ReceptionQueueEntry.query.filter(ReceptionQueueEntry.queue_date == _today())
    if status:
        query = query.filter(ReceptionQueueEntry.status == status)
    return query.order_by(ReceptionQueueEntry.daily_sequence.asc()).all()


def recent_activity(limit: int = 30) -> list[ReceptionActivityLog]:
    if not table_exists_name("reception_activity_logs"):
        return []
    return ReceptionActivityLog.query.order_by(ReceptionActivityLog.created_at.desc()).limit(limit).all()


def get_kpis() -> dict[str, Any]:
    today = _today()
    today_start = datetime.combine(today, datetime.min.time())
    queue_entries = today_queue_entries()
    waiting = sum(1 for e in queue_entries if e.status == STATUS_WAITING)
    checked_in = sum(1 for e in queue_entries if e.status == STATUS_CHECKED_IN)
    checked_out = sum(1 for e in queue_entries if e.status == STATUS_CHECKED_OUT)
    patient_ids = {e.patient_id for e in queue_entries}
    new_registrations = Patient.query.filter(Patient.created_at >= today_start).count()
    pending_payment = sum(1 for e in queue_entries if (e.payment_status or "").upper() == "PENDING")
    try:
        from app.models.biz_order import BizInvoice
        from app.business_engine.statuses import INVOICE_UNPAID

        pending_payment = max(
            pending_payment,
            BizInvoice.query.filter_by(status=INVOICE_UNPAID).count(),
        )
    except Exception:
        db.session.rollback()
    avg_wait_minutes = 0
    completed = [e for e in queue_entries if e.checked_in_at and e.created_at]
    if completed:
        total = sum((e.checked_in_at - e.created_at).total_seconds() for e in completed)
        avg_wait_minutes = round(total / len(completed) / 60, 1)
    return {
        "date": today.isoformat(),
        "todays_patients": len(patient_ids),
        "waiting_queue": waiting,
        "checked_in": checked_in,
        "checked_out": checked_out,
        "pending_payment": pending_payment,
        "new_registrations": new_registrations,
        "total_queue_entries": len(queue_entries),
        "avg_wait_minutes": avg_wait_minutes,
    }


def dashboard_payload() -> dict[str, Any]:
    entries = today_queue_entries()
    patients_by_code = {
        p.patient_code: p
        for p in Patient.query.filter(
            Patient.patient_code.in_([e.patient_id for e in entries] or [""])
        ).all()
    }
    waiting = [e for e in entries if e.status == STATUS_WAITING]
    checked_in = [e for e in entries if e.status == STATUS_CHECKED_IN]
    checked_out = [e for e in entries if e.status == STATUS_CHECKED_OUT]
    todays_patients = Patient.query.filter(Patient.created_at >= datetime.combine(_today(), datetime.min.time())).all()
    upcoming = []
    if table_exists_name("clinic_bookings"):
        upcoming = (
            ClinicBooking.query.filter(
                ClinicBooking.status.in_(("PENDING", "CONFIRMED", "SCHEDULED")),
                func.date(ClinicBooking.scheduled_at) == _today(),
            )
            .order_by(ClinicBooking.scheduled_at.asc())
            .limit(10)
            .all()
        )
    return {
        "kpis": get_kpis(),
        "waiting_queue": [serialize_queue(e, patients_by_code) for e in waiting],
        "checked_in": [serialize_queue(e, patients_by_code) for e in checked_in],
        "checked_out": [serialize_queue(e, patients_by_code) for e in checked_out],
        "todays_patients": [p.to_dict() for p in todays_patients[:20]],
        "upcoming_appointments": [b.to_dict() for b in upcoming],
        "activity": [a.to_dict() for a in recent_activity(10)],
    }


def serialize_queue(entry: ReceptionQueueEntry, patients: dict[str, Patient]) -> dict[str, Any]:
    patient = patients.get(entry.patient_id)
    wait_minutes = 0
    if entry.created_at:
        wait_minutes = int((datetime.utcnow() - entry.created_at).total_seconds() // 60)
    payload = entry.to_dict()
    payload["patient_name"] = patient.full_name if patient else entry.patient_id
    payload["patient_phone"] = patient.phone if patient else ""
    payload["wait_minutes"] = wait_minutes
    return payload
