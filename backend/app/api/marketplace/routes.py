from flask import Blueprint, request

from app.services.marketplace_booking import MarketplaceBookingError, MarketplaceBookingService
from app.services.marketplace_search import MarketplaceSearchService


marketplace_bp = Blueprint(
    "marketplace",
    __name__,
    url_prefix="/api/v1/marketplace",
)


def _client_ip():
    return request.remote_addr or ""


def _actor_email():
    return request.headers.get("X-User-Email", "SYSTEM")


@marketplace_bp.route("/search", methods=["GET"])
def marketplace_search():
    payload = MarketplaceSearchService.search(
        q=request.args.get("q"),
        province=request.args.get("province"),
        city=request.args.get("city"),
        district=request.args.get("district"),
        partner_type=request.args.get("partner_type"),
        home_collection=request.args.get("home_collection"),
        max_price=request.args.get("max_price"),
        sort=request.args.get("sort", "relevance"),
        date=request.args.get("date"),
    )
    return payload


@marketplace_bp.route("/bookings", methods=["GET"])
def list_bookings():
    bookings = MarketplaceBookingService.list_bookings(
        status=request.args.get("status"),
        partner_id=request.args.get("partner_id"),
    )

    return {
        "count": len(bookings),
        "bookings": [booking.to_dict() for booking in bookings],
    }


@marketplace_bp.route("/bookings", methods=["POST"])
def create_booking():
    data = request.get_json(silent=True) or {}

    try:
        booking = MarketplaceBookingService.create_booking(
            data,
            actor_email=_actor_email(),
            ip_address=_client_ip(),
        )
    except MarketplaceBookingError as exc:
        return {"error": exc.message}, exc.status_code

    return {
        "message": "Booking created successfully",
        "booking": booking.to_dict(),
    }, 201


@marketplace_bp.route("/bookings/<booking_id>", methods=["GET"])
def get_booking(booking_id):
    try:
        booking = MarketplaceBookingService.get_booking_detail(booking_id)
    except MarketplaceBookingError as exc:
        return {"error": exc.message}, exc.status_code

    return booking


@marketplace_bp.route("/bookings/<booking_id>/transition", methods=["POST"])
def transition_booking(booking_id):
    data = request.get_json(silent=True) or {}
    event_type = data.get("event_type")

    if not event_type:
        return {"error": "event_type is required"}, 400

    try:
        booking = MarketplaceBookingService.transition_booking(
            booking_id,
            event_type,
            message=data.get("message"),
            actor_email=_actor_email(),
            ip_address=_client_ip(),
            update_status=data.get("update_status", True),
        )
    except MarketplaceBookingError as exc:
        return {"error": exc.message}, exc.status_code

    return {
        "message": "Booking transitioned successfully",
        "booking": booking.to_dict(),
        "timeline": [
            event.to_dict()
            for event in MarketplaceBookingService.list_booking_timeline(booking_id)
        ],
    }


@marketplace_bp.route("/bookings/<booking_id>/timeline", methods=["GET"])
def get_booking_timeline(booking_id):
    try:
        timeline = MarketplaceBookingService.list_booking_timeline(booking_id)
    except MarketplaceBookingError as exc:
        return {"error": exc.message}, exc.status_code

    return {
        "count": len(timeline),
        "timeline": [event.to_dict() for event in timeline],
    }
