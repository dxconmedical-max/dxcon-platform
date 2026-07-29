"""Sample Collection production API."""

from __future__ import annotations

from flask import Blueprint, request, session

from app.extensions.db import db
from app.sample_collection_workspace.auth import collection_api_read, collection_api_write
from app.sample_collection_workspace.service import (
    collect_from_queue,
    list_production_queue,
    workspace_dashboard,
)
from app.services.sample_collection_workflow import (
    SampleCollectionWorkflowError,
    SampleCollectionWorkflowService,
)


sample_collections_bp = Blueprint(
    "sample_collections",
    __name__,
    url_prefix="/api/v1/sample-collections",
)


def _client_ip() -> str:
    return request.remote_addr or ""


def _actor() -> str:
    return (
        session.get("email")
        or request.headers.get("X-Actor")
        or request.headers.get("X-User-Email")
        or "SYSTEM"
    )


def _role() -> str | None:
    return session.get("role") or request.headers.get("X-User-Role")


def _scoped_collector_id() -> str | None:
    return (
        request.headers.get("X-Collector-Id")
        or session.get("collector_id")
        or request.args.get("scoped_collector_id")
    )


@sample_collections_bp.route("/dashboard", methods=["GET"])
@collection_api_read
def dashboard():
    return {"success": True, "data": workspace_dashboard()}, 200


@sample_collections_bp.route("/queue", methods=["GET"])
@collection_api_read
def queue():
    """Field collector queue by default (HOME_COLLECTION / CLINIC_COLLECTION)."""
    try:
        payload = list_production_queue(
            status=request.args.get("status"),
            collector_id=request.args.get("collector"),
            location=request.args.get("location"),
            date_from=request.args.get("date") or request.args.get("date_from"),
            date_to=request.args.get("date_to"),
            partner_id=request.args.get("partner_id") or request.headers.get("X-Partner-Id"),
            include_desk=False,
            queue=request.args.get("queue") or "field",
            role=_role(),
            scoped_collector_id=_scoped_collector_id(),
            organization_id=request.headers.get("X-Organization-ID")
            or request.headers.get("X-Organization-Id"),
        )
    except SampleCollectionWorkflowError as exc:
        code = "SERVICE_UNAVAILABLE" if exc.status_code == 503 else "WORKFLOW_ERROR"
        return {
            "success": False,
            "error": {"code": code, "message": exc.message},
        }, exc.status_code
    return {"success": True, "data": payload}, 200


@sample_collections_bp.route("/<collection_id>", methods=["GET"])
@collection_api_read
def get_collection(collection_id):
    try:
        from app.sample_collection_workspace.collection_routing import annotate_collection_payload

        payload = annotate_collection_payload(
            SampleCollectionWorkflowService.get_collection(collection_id)
        )
    except SampleCollectionWorkflowError as exc:
        return {"success": False, "error": exc.message}, exc.status_code
    return {"success": True, "data": payload}, 200


@sample_collections_bp.route("/bookings/<booking_id>/ensure", methods=["POST"])
@collection_api_write
def ensure_for_booking(booking_id):
    try:
        collection = SampleCollectionWorkflowService.ensure_collection_for_booking(
            booking_id,
            actor_email=_actor(),
            ip_address=_client_ip(),
        )
    except SampleCollectionWorkflowError as exc:
        db.session.rollback()
        return {"success": False, "error": exc.message}, exc.status_code
    return {
        "success": True,
        "data": SampleCollectionWorkflowService._enrich_payload(collection),
    }, 200


@sample_collections_bp.route("/<collection_id>/verify", methods=["POST"])
@collection_api_write
def verify(collection_id):
    data = request.get_json(silent=True) or {}
    try:
        collection = SampleCollectionWorkflowService.verify_identifiers(
            collection_id,
            patient_name=data.get("patient_name"),
            booking_code=data.get("booking_code"),
            order_id=data.get("order_id"),
            scanned_barcode=data.get("scanned_barcode") or data.get("barcode"),
            actor_email=_actor(),
            ip_address=_client_ip(),
        )
    except SampleCollectionWorkflowError as exc:
        db.session.rollback()
        return {"success": False, "error": exc.message}, exc.status_code
    return {
        "success": True,
        "data": SampleCollectionWorkflowService._enrich_payload(collection),
    }, 200


@sample_collections_bp.route("/<collection_id>/collect", methods=["POST"])
@collection_api_write
def collect(collection_id):
    data = request.get_json(silent=True) or {}
    try:
        result = collect_from_queue(
            collection_id,
            data,
            actor=_actor(),
            ip_address=_client_ip(),
        )
    except SampleCollectionWorkflowError as exc:
        db.session.rollback()
        return {"success": False, "error": exc.message}, exc.status_code
    return {"success": True, "data": result}, 200


@sample_collections_bp.route("/<collection_id>/reject", methods=["POST"])
@collection_api_write
def reject(collection_id):
    data = request.get_json(silent=True) or {}
    quality = data.get("quality_status") or data.get("reason_code")
    if not quality:
        return {"success": False, "error": "quality_status is required"}, 400
    try:
        collection, recollect = SampleCollectionWorkflowService.reject_specimen(
            collection_id,
            quality_status=quality,
            rejection_reason=data.get("rejection_reason") or data.get("note"),
            actor_email=_actor(),
            ip_address=_client_ip(),
            request_recollect=data.get("request_recollect", True),
        )
    except SampleCollectionWorkflowError as exc:
        db.session.rollback()
        return {"success": False, "error": exc.message}, exc.status_code
    return {
        "success": True,
        "data": {
            "collection": SampleCollectionWorkflowService._enrich_payload(collection),
            "recollect": SampleCollectionWorkflowService._enrich_payload(recollect)
            if recollect
            else None,
        },
    }, 200


@sample_collections_bp.route("/<collection_id>/recollect", methods=["POST"])
@collection_api_write
def recollect(collection_id):
    data = request.get_json(silent=True) or {}
    try:
        row = SampleCollectionWorkflowService.request_recollect(
            collection_id,
            actor_email=_actor(),
            ip_address=_client_ip(),
            specimen_type=data.get("specimen_type"),
        )
    except SampleCollectionWorkflowError as exc:
        db.session.rollback()
        return {"success": False, "error": exc.message}, exc.status_code
    return {
        "success": True,
        "data": SampleCollectionWorkflowService._enrich_payload(row),
    }, 200


@sample_collections_bp.route("/bookings/<booking_id>/dispatch", methods=["POST"])
@collection_api_write
def dispatch(booking_id):
    data = request.get_json(silent=True) or {}
    try:
        collection, sample = SampleCollectionWorkflowService.dispatch_sample(
            booking_id,
            transport_box_id=data.get("transport_box_id"),
            note=data.get("note"),
            actor_email=_actor(),
            ip_address=_client_ip(),
            vehicle_id=data.get("vehicle_id"),
            driver_id=data.get("driver_id"),
            distance_km=data.get("distance_km"),
            eta_minutes=data.get("eta_minutes"),
            temperature_c=data.get("temperature_c"),
            iot_device_id=data.get("iot_device_id"),
        )
    except SampleCollectionWorkflowError as exc:
        db.session.rollback()
        return {"success": False, "error": exc.message}, exc.status_code
    return {
        "success": True,
        "data": {
            "collection": SampleCollectionWorkflowService._enrich_payload(collection),
            "sample_tracking": sample.to_dict(),
        },
    }, 200


@sample_collections_bp.route("/<collection_id>/dispatch", methods=["POST"])
@collection_api_write
def dispatch_by_collection(collection_id):
    """Dispatch / transport by collection id (desk + field)."""
    data = request.get_json(silent=True) or {}
    try:
        collection, sample = SampleCollectionWorkflowService.dispatch_by_collection_id(
            collection_id,
            transport_box_id=data.get("transport_box_id"),
            note=data.get("note"),
            actor_email=_actor(),
            ip_address=_client_ip(),
            vehicle_id=data.get("vehicle_id"),
            driver_id=data.get("driver_id"),
            distance_km=data.get("distance_km"),
            eta_minutes=data.get("eta_minutes"),
            temperature_c=data.get("temperature_c"),
            iot_device_id=data.get("iot_device_id"),
        )
    except SampleCollectionWorkflowError as exc:
        db.session.rollback()
        return {"success": False, "error": exc.message}, exc.status_code
    return {
        "success": True,
        "data": {
            "collection": SampleCollectionWorkflowService._enrich_payload(collection),
            "sample_tracking": sample.to_dict(),
        },
    }, 200


@sample_collections_bp.route("/<collection_id>/handoff", methods=["POST"])
@collection_api_write
def handoff(collection_id):
    data = request.get_json(silent=True) or {}
    try:
        collection = SampleCollectionWorkflowService.record_handoff(
            collection_id,
            note=data.get("note"),
            temperature_c=data.get("temperature_c"),
            actor_email=_actor(),
            ip_address=_client_ip(),
        )
        # Desk bridge: after handoff → IN_TRANSIT, sync sample queue
        if not collection.marketplace_booking_id:
            from app.sample_collection_workspace.desk_bridge import (
                enqueue_sample_and_lab_after_transition,
                sync_biz_collection_from_sample,
            )

            sync_biz_collection_from_sample(collection, actor=_actor())
            enqueue_sample_and_lab_after_transition(collection, actor=_actor())
            db.session.commit()
    except SampleCollectionWorkflowError as exc:
        db.session.rollback()
        return {"success": False, "error": exc.message}, exc.status_code
    return {
        "success": True,
        "data": SampleCollectionWorkflowService._enrich_payload(collection),
    }, 200


@sample_collections_bp.route("/bookings/<booking_id>/lab-arrive", methods=["POST"])
@collection_api_write
def lab_arrive(booking_id):
    data = request.get_json(silent=True) or {}
    try:
        collection, sample = SampleCollectionWorkflowService.receive_at_lab(
            booking_id,
            note=data.get("note"),
            actor_email=_actor(),
            ip_address=_client_ip(),
            temperature_c=data.get("temperature_c"),
        )
    except SampleCollectionWorkflowError as exc:
        db.session.rollback()
        return {"success": False, "error": exc.message}, exc.status_code
    return {
        "success": True,
        "data": {
            "collection": SampleCollectionWorkflowService._enrich_payload(collection),
            "sample_tracking": sample.to_dict(),
            "synthetic_specimen_id": sample.sample_code,
        },
    }, 200


@sample_collections_bp.route("/<collection_id>/lab-arrive", methods=["POST"])
@collection_api_write
def lab_arrive_by_collection(collection_id):
    """Lab arrival by collection id (desk + field)."""
    data = request.get_json(silent=True) or {}
    try:
        collection, sample = SampleCollectionWorkflowService.receive_by_collection_id(
            collection_id,
            note=data.get("note"),
            actor_email=_actor(),
            ip_address=_client_ip(),
            temperature_c=data.get("temperature_c"),
        )
    except SampleCollectionWorkflowError as exc:
        db.session.rollback()
        return {"success": False, "error": exc.message}, exc.status_code
    return {
        "success": True,
        "data": {
            "collection": SampleCollectionWorkflowService._enrich_payload(collection),
            "sample_tracking": sample.to_dict(),
            "synthetic_specimen_id": sample.sample_code,
        },
    }, 200


@sample_collections_bp.route("/collectors", methods=["GET"])
@collection_api_read
def list_collectors():
    from app.sample_collection_workspace.collection_routing import list_assignable_collectors

    org = request.headers.get("X-Organization-ID") or request.headers.get("X-Organization-Id")
    return {
        "success": True,
        "data": {"items": list_assignable_collectors(organization_id=org)},
    }, 200


@sample_collections_bp.route("/<collection_id>/assign", methods=["POST"])
@collection_api_write
def assign_collection_collector(collection_id):
    """Assign or reassign a field collector (HOME/CLINIC)."""
    from app.sample_collection_workspace.collection_domain import CollectionDomainError
    from app.sample_collection_workspace.collection_routing import assign_collector

    data = request.get_json(silent=True) or {}
    try:
        collection = assign_collector(
            collection_id,
            collector_id=data.get("collector_id") or "",
            collector_name=data.get("collector_name"),
            actor=_actor(),
        )
        db.session.commit()
    except CollectionDomainError as exc:
        db.session.rollback()
        return {"success": False, "error": exc.message}, exc.status_code
    return {
        "success": True,
        "data": SampleCollectionWorkflowService._enrich_payload(collection),
    }, 200


@sample_collections_bp.route("/<collection_id>/unassign", methods=["POST"])
@collection_api_write
def unassign_collection_collector(collection_id):
    """Release collector assignment → PENDING_ASSIGNMENT."""
    from app.sample_collection_workspace.collection_domain import CollectionDomainError
    from app.sample_collection_workspace.collection_routing import release_collector_assignment

    try:
        collection = release_collector_assignment(collection_id, actor=_actor())
        db.session.commit()
    except CollectionDomainError as exc:
        db.session.rollback()
        return {"success": False, "error": exc.message}, exc.status_code
    return {
        "success": True,
        "data": SampleCollectionWorkflowService._enrich_payload(collection),
    }, 200


@sample_collections_bp.route("/<collection_id>/transport", methods=["GET"])
@collection_api_read
def transport(collection_id):
    try:
        payload = SampleCollectionWorkflowService.transport_status(collection_id)
    except SampleCollectionWorkflowError as exc:
        return {"success": False, "error": exc.message}, exc.status_code
    return {"success": True, "data": payload}, 200


@sample_collections_bp.route("/<collection_id>/audit", methods=["GET"])
@collection_api_read
def audit_trail(collection_id):
    try:
        payload = SampleCollectionWorkflowService.get_audit_trail(collection_id)
    except SampleCollectionWorkflowError as exc:
        return {"success": False, "error": exc.message}, exc.status_code
    return {"success": True, "data": payload}, 200


# Legacy CRUD kept for compatibility (auth-gated)
@sample_collections_bp.route("", methods=["GET"])
@collection_api_read
def get_sample_collections():
    try:
        items = SampleCollectionWorkflowService.list_queue(awaiting_only=False)
    except SampleCollectionWorkflowError as exc:
        return {"error": exc.message}, exc.status_code
    return {"count": len(items), "collections": items}


@sample_collections_bp.route("", methods=["POST"])
@collection_api_write
def create_sample_collection():
    data = request.get_json(silent=True) or {}
    booking_id = data.get("marketplace_booking_id") or data.get("booking_id")
    if not booking_id:
        return {"success": False, "error": "marketplace_booking_id is required"}, 400
    try:
        collection = SampleCollectionWorkflowService.ensure_collection_for_booking(
            booking_id,
            actor_email=_actor(),
            ip_address=_client_ip(),
        )
    except SampleCollectionWorkflowError as exc:
        db.session.rollback()
        return {"success": False, "error": exc.message}, exc.status_code
    return {
        "message": "Sample collection created",
        "collection": SampleCollectionWorkflowService._enrich_payload(collection),
    }, 201
