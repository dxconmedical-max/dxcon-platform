from flask import Blueprint, request
from datetime import datetime
import uuid

from app.extensions.db import db
from app.models.home_collection import HomeCollection
from app.models.sample_tracking import SampleTracking
from app.models.sample_event import SampleEvent
from app.models.driver import Driver
from app.core.statuses import (
    BOOKING_PENDING,
    BOOKING_ASSIGNED,
    BOOKING_CHECKED_IN,
    BOOKING_COLLECTED,
    SAMPLE_IN_TRANSIT,
    SAMPLE_RECEIVED,
    SAMPLE_PROCESSING,
    SAMPLE_COMPLETED,
)

workflow_bp = Blueprint(
    "workflow",
    __name__,
    url_prefix="/api/v1/workflow"
)


def sample_code():
    return "SMP-" + datetime.utcnow().strftime("%Y%m%d") + "-" + str(uuid.uuid4())[:8].upper()


def event(sample_id, event_type, note):
    e = SampleEvent(
        sample_tracking_id=sample_id,
        event_type=event_type,
        note=note
    )
    db.session.add(e)


def safe_set(obj, field, value):
    if hasattr(obj, field) and value is not None:
        setattr(obj, field, value)


@workflow_bp.route("/health")
def health():
    return {
        "status": "ok",
        "service": "dxcon-workflow"
    }


@workflow_bp.route("/bookings", methods=["GET"])
def bookings():
    items = HomeCollection.query.order_by(
        HomeCollection.created_at.desc()
        if hasattr(HomeCollection, "created_at")
        else HomeCollection.id.desc()
    ).all()

    return {
        "count": len(items),
        "bookings": [i.to_dict() for i in items]
    }


@workflow_bp.route("/bookings", methods=["POST"])
def create_booking():
    data = request.json or {}

    booking = HomeCollection(
        patient_id=data.get("patient_id"),
        address=data.get("address"),
        scheduled_time=data.get("scheduled_time"),
        status=BOOKING_PENDING
    )

    safe_set(booking, "note", data.get("note"))
    safe_set(booking, "phone", data.get("phone"))

    db.session.add(booking)
    db.session.commit()

    return {
        "success": True,
        "booking": booking.to_dict()
    }, 201


@workflow_bp.route("/assign/<booking_id>/<collector_id>", methods=["POST", "GET"])
def assign(booking_id, collector_id):
    booking = HomeCollection.query.get(booking_id)
    collector = Driver.query.get(collector_id)

    if not booking:
        return {"error": "Booking not found"}, 404

    if not collector:
        return {"error": "Collector not found"}, 404

    safe_set(booking, "collector_id", collector_id)
    booking.status = BOOKING_ASSIGNED

    db.session.commit()

    return {
        "success": True,
        "booking": booking.to_dict()
    }


@workflow_bp.route("/checkin/<booking_id>", methods=["POST", "GET"])
def checkin(booking_id):
    booking = HomeCollection.query.get(booking_id)

    if not booking:
        return {"error": "Booking not found"}, 404

    booking.status = BOOKING_CHECKED_IN
    db.session.commit()

    return {
        "success": True,
        "booking": booking.to_dict()
    }


@workflow_bp.route("/collected/<booking_id>", methods=["POST", "GET"])
def collected(booking_id):
    data = request.json or {}

    booking = HomeCollection.query.get(booking_id)

    if not booking:
        return {"error": "Booking not found"}, 404

    booking.status = BOOKING_COLLECTED

    sample = SampleTracking.query.filter_by(
        home_collection_id=booking.id
    ).first()

    if not sample:
        sample = SampleTracking(
            sample_code=sample_code(),
            home_collection_id=booking.id,
            status=SAMPLE_IN_TRANSIT
        )
        db.session.add(sample)
        db.session.flush()

    safe_set(sample, "collector_id", data.get("collector_id") or getattr(booking, "collector_id", None))
    safe_set(sample, "transport_box_id", data.get("transport_box_id"))
    safe_set(sample, "latitude", data.get("latitude"))
    safe_set(sample, "longitude", data.get("longitude"))

    sample.status = SAMPLE_IN_TRANSIT

    event(sample.id, BOOKING_COLLECTED, "Sample collected at patient location")
    event(sample.id, SAMPLE_IN_TRANSIT, "Sample is in transit to laboratory")

    db.session.commit()

    return {
        "success": True,
        "booking": booking.to_dict(),
        "sample": sample.to_dict()
    }


@workflow_bp.route("/sample/<sample_id>/<status>", methods=["POST", "GET"])
def update_sample_status(sample_id, status):
    sample = SampleTracking.query.get(sample_id)

    if not sample:
        return {"error": "Sample not found"}, 404

    status = status.upper()

    allowed = [
        SAMPLE_RECEIVED,
        SAMPLE_PROCESSING,
        SAMPLE_COMPLETED,
    ]

    if status not in allowed:
        return {"error": "Invalid status"}, 400

    sample.status = status

    event(
        sample.id,
        status,
        f"Sample status updated to {status}"
    )

    db.session.commit()

    return {
        "success": True,
        "sample": sample.to_dict()
    }


@workflow_bp.route("/dashboard")
def dashboard():
    bookings = HomeCollection.query.all()
    samples = SampleTracking.query.all()

    return {
        "bookings": {
            "total": len(bookings),
            "pending": len([b for b in bookings if b.status == BOOKING_PENDING]),
            "assigned": len([b for b in bookings if b.status == BOOKING_ASSIGNED]),
            "checked_in": len([b for b in bookings if b.status == BOOKING_CHECKED_IN]),
            "collected": len([b for b in bookings if b.status == BOOKING_COLLECTED]),
        },
        "samples": {
            "total": len(samples),
            "in_transit": len([s for s in samples if s.status == SAMPLE_IN_TRANSIT]),
            "received": len([s for s in samples if s.status == SAMPLE_RECEIVED]),
            "processing": len([s for s in samples if s.status == SAMPLE_PROCESSING]),
            "completed": len([s for s in samples if s.status == SAMPLE_COMPLETED]),
        }
    }
