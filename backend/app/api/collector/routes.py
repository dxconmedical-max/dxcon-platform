from flask import Blueprint, request
from datetime import datetime
import uuid

from app.extensions.db import db
from app.models.driver import Driver
from app.models.home_collection import HomeCollection
from app.models.sample_tracking import SampleTracking
from app.models.sample_event import SampleEvent


collector_bp = Blueprint(
    "collector",
    __name__,
    url_prefix="/api/v1/collector"
)


def generate_sample_code():
    today = datetime.utcnow().strftime("%Y%m%d")
    short_id = str(uuid.uuid4())[:8].upper()
    return f"SMP-{today}-{short_id}"


def create_sample_event(sample_id, event_type, note=""):
    event = SampleEvent(
        sample_tracking_id=sample_id,
        event_type=event_type,
        note=note
    )
    db.session.add(event)


@collector_bp.route("/collectors", methods=["GET"])
def list_collectors():
    collectors = Driver.query.all()
    return {
        "count": len(collectors),
        "collectors": [item.to_dict() for item in collectors]
    }


@collector_bp.route("/collectors", methods=["POST"])
def create_collector():
    data = request.json or {}

    collector_code = data.get("collector_code") or data.get("driver_code")
    full_name = data.get("full_name")

    if not collector_code:
        return {"error": "collector_code is required"}, 400

    if not full_name:
        return {"error": "full_name is required"}, 400

    existing = Driver.query.filter_by(driver_code=collector_code).first()

    if existing:
        return {"error": "Collector code already exists"}, 409

    collector = Driver(
        driver_code=collector_code,
        full_name=full_name,
        phone=data.get("phone"),
        vehicle_no=data.get("vehicle_no"),
        status=data.get("status") or "ACTIVE"
    )

    db.session.add(collector)
    db.session.commit()

    return {
        "success": True,
        "collector": collector.to_dict()
    }, 201


@collector_bp.route("/jobs", methods=["GET"])
def jobs():
    items = HomeCollection.query.all()
    return {
        "count": len(items),
        "jobs": [item.to_dict() for item in items]
    }


@collector_bp.route("/checkin/<job_id>", methods=["POST", "GET"])
def checkin(job_id):
    job = HomeCollection.query.get(job_id)

    if not job:
        return {"error": "Job not found"}, 404

    job.status = "CHECKED_IN"
    db.session.commit()

    return {
        "success": True,
        "job": job.to_dict()
    }


@collector_bp.route("/collected/<job_id>", methods=["POST", "GET"])
def collected(job_id):
    data = request.json or {}

    job = HomeCollection.query.get(job_id)

    if not job:
        return {"error": "Job not found"}, 404

    collector_id = data.get("collector_id") or job.collector_id
    transport_box_id = data.get("transport_box_id")
    latitude = data.get("latitude")
    longitude = data.get("longitude")

    job.status = "COLLECTED"

    sample = SampleTracking.query.filter_by(
        home_collection_id=job.id
    ).first()

    if not sample:
        sample = SampleTracking(
            sample_code=generate_sample_code(),
            home_collection_id=job.id,
            collector_id=collector_id,
            transport_box_id=transport_box_id,
            latitude=latitude,
            longitude=longitude,
            status="IN_TRANSIT"
        )
        db.session.add(sample)
        db.session.flush()

        create_sample_event(
            sample.id,
            "COLLECTED",
            "Sample collected at patient home"
        )
    else:
        sample.status = "IN_TRANSIT"
        sample.collector_id = collector_id or sample.collector_id
        sample.transport_box_id = transport_box_id or sample.transport_box_id
        sample.latitude = latitude or sample.latitude
        sample.longitude = longitude or sample.longitude

    create_sample_event(
        sample.id,
        "IN_TRANSIT",
        "Sample is in transit to laboratory"
    )

    db.session.commit()

    return {
        "success": True,
        "job": job.to_dict(),
        "sample": sample.to_dict()
    }


@collector_bp.route("/received/<sample_id>", methods=["POST", "GET"])
def received(sample_id):
    sample = SampleTracking.query.get(sample_id)

    if not sample:
        return {"error": "Sample not found"}, 404

    sample.status = "RECEIVED"

    create_sample_event(
        sample.id,
        "RECEIVED",
        "Sample received by laboratory"
    )

    db.session.commit()

    return {
        "success": True,
        "sample": sample.to_dict()
    }


@collector_bp.route("/processing/<sample_id>", methods=["POST", "GET"])
def processing(sample_id):
    sample = SampleTracking.query.get(sample_id)

    if not sample:
        return {"error": "Sample not found"}, 404

    sample.status = "PROCESSING"

    create_sample_event(
        sample.id,
        "PROCESSING",
        "Sample is being processed by laboratory"
    )

    db.session.commit()

    return {
        "success": True,
        "sample": sample.to_dict()
    }


@collector_bp.route("/completed/<sample_id>", methods=["POST", "GET"])
def completed(sample_id):
    sample = SampleTracking.query.get(sample_id)

    if not sample:
        return {"error": "Sample not found"}, 404

    sample.status = "COMPLETED"

    create_sample_event(
        sample.id,
        "COMPLETED",
        "Sample workflow completed"
    )

    db.session.commit()

    return {
        "success": True,
        "sample": sample.to_dict()
    }


@collector_bp.route("/samples", methods=["GET"])
def samples():
    items = SampleTracking.query.order_by(
        SampleTracking.created_at.desc()
    ).all()

    return {
        "count": len(items),
        "samples": [item.to_dict() for item in items]
    }
