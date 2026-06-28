from flask import Blueprint, request

from app.services.booking_assignment import BookingAssignmentError, BookingAssignmentService
from app.services.scheduling import SchedulingError, SchedulingService
from app.services.slot_generation import SlotGenerationService


scheduling_bp = Blueprint(
    "scheduling",
    __name__,
    url_prefix="/api/v1/scheduling",
)


def _client_ip():
    return request.remote_addr or ""


def _actor_email():
    return request.headers.get("X-User-Email", "SYSTEM")


@scheduling_bp.route("/partners/<partner_id>/slots", methods=["GET"])
def list_partner_slots(partner_id):
    try:
        slots = SchedulingService.list_available_slots(
            partner_id,
            slot_date=request.args.get("date"),
            slot_type=request.args.get("slot_type", "COLLECTION"),
            include_full=request.args.get("include_full", "").lower() in ("1", "true", "yes"),
        )
    except SchedulingError as exc:
        return {"error": exc.message}, exc.status_code

    return {
        "count": len(slots),
        "slots": [slot.to_dict() for slot in slots],
    }


@scheduling_bp.route("/partners/<partner_id>/generate-slots", methods=["POST"])
def generate_partner_slots(partner_id):
    data = request.get_json(silent=True) or {}

    try:
        created = SlotGenerationService.generate_partner_daily_slots(
            partner_id,
            days=int(data.get("days", 7)),
            slot_type=data.get("slot_type", "COLLECTION"),
            slot_capacity=int(data.get("slot_capacity", 5)),
            start_date=data.get("start_date"),
        )
    except (SchedulingError, ValueError) as exc:
        message = getattr(exc, "message", str(exc))
        status = getattr(exc, "status_code", 400)
        return {"error": message}, status

    return {
        "message": "Partner slots generated successfully",
        "created": created,
    }


@scheduling_bp.route("/bookings/<booking_id>/reserve-slot", methods=["POST"])
def reserve_booking_slot(booking_id):
    data = request.get_json(silent=True) or {}
    slot_id = data.get("slot_id")

    if not slot_id:
        return {"error": "slot_id is required"}, 400

    try:
        booking, slot = BookingAssignmentService.reserve_slot_for_booking(
            booking_id,
            slot_id,
            actor_email=_actor_email(),
            ip_address=_client_ip(),
        )
    except BookingAssignmentError as exc:
        return {"error": exc.message}, exc.status_code

    return {
        "message": "Slot reserved successfully",
        "booking": booking.to_dict(),
        "slot": slot.to_dict(),
    }


@scheduling_bp.route("/bookings/<booking_id>/assign-collector", methods=["POST"])
def assign_booking_collector(booking_id):
    data = request.get_json(silent=True) or {}

    try:
        assignment = BookingAssignmentService.assign_collector(
            booking_id,
            collector_id=data.get("collector_id"),
            note=data.get("note"),
            actor_email=_actor_email(),
            ip_address=_client_ip(),
        )
    except BookingAssignmentError as exc:
        return {"error": exc.message}, exc.status_code

    return {
        "message": "Collector assigned successfully",
        "assignment": assignment.to_dict(),
    }


@scheduling_bp.route("/collectors/availability", methods=["GET"])
def list_collector_availability():
    records = BookingAssignmentService.list_collector_availability(
        city=request.args.get("city"),
        district=request.args.get("district"),
        date=request.args.get("date"),
    )

    return {
        "count": len(records),
        "availability": [record.to_dict() for record in records],
    }
