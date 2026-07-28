"""Reception operational workspace REST API — Sprint 006."""

from __future__ import annotations

from flask import Blueprint, request, session

from app.business_engine.service import BusinessEngineError
from app.extensions.db import db
from app.reception_workspace.auth import reception_api_read, reception_api_write
from app.reception_workspace.service import (
    ReceptionWorkspaceError,
    collect_payment,
    create_collection_after_payment,
    create_reception_order,
    fast_search_patients,
    generate_barcodes,
    get_lab_handoff_status,
    get_order_with_payment,
    get_payment_history,
    get_patient_profile,
    handoff_to_laboratory,
    payment_report,
    queue_report,
    reception_workspace_report,
    register_patient,
    render_request_form,
    search_tests,
    workspace_dashboard,
)

reception_workspace_bp = Blueprint("reception_workspace", __name__, url_prefix="/api/v1/reception/workspace")


def _actor() -> str | None:
    return session.get("email") or request.headers.get("X-Actor") or request.headers.get("X-User-Email")


@reception_workspace_bp.route("/dashboard", methods=["GET"])
@reception_api_read
def dashboard():
    return {"success": True, "data": workspace_dashboard()}, 200


@reception_workspace_bp.route("/search", methods=["GET"])
@reception_api_read
def search():
    result = fast_search_patients(
        request.args.get("q") or request.args.get("query") or "",
        limit=int(request.args.get("limit", request.args.get("per_page", 20))),
        page=int(request.args.get("page", 1)),
    )
    return {"success": True, **result}, 200


@reception_workspace_bp.route("/patients/register", methods=["POST"])
@reception_api_write
def patients_register():
    payload = request.get_json(silent=True) or {}
    try:
        result = register_patient(payload, actor=_actor(), force=bool(payload.get("force")))
        if result.get("duplicate") and not result.get("ok"):
            return {"success": False, "duplicate": True, "warnings": result.get("warnings", [])}, 409
        db.session.commit()
        return {"success": True, "data": result}, 201
    except (ReceptionWorkspaceError, BusinessEngineError) as exc:
        db.session.rollback()
        return {"success": False, "error": str(exc)}, 400


@reception_workspace_bp.route("/patients/<patient_code>", methods=["GET"])
@reception_api_read
def patient_profile(patient_code: str):
    try:
        return {"success": True, "data": get_patient_profile(patient_code)}, 200
    except ReceptionWorkspaceError as exc:
        return {"success": False, "error": str(exc)}, 404


@reception_workspace_bp.route("/tests", methods=["GET"])
@reception_api_read
def tests_search():
    result = search_tests(
        query=request.args.get("q"),
        category=request.args.get("category"),
        department=request.args.get("department"),
        limit=int(request.args.get("limit", 50)),
        page=int(request.args.get("page", 1)),
    )
    return {"success": True, **result}, 200


@reception_workspace_bp.route("/orders", methods=["POST"])
@reception_api_write
def orders_create():
    payload = request.get_json(silent=True) or {}
    try:
        organization_id = (
            request.headers.get("X-Organization-ID")
            or request.headers.get("X-Organization-Id")
            or payload.get("organization_id")
        )
        result = create_reception_order(
            patient_code=payload.get("patient_code", ""),
            test_catalog_ids=payload.get("test_catalog_ids") or payload.get("tests") or [],
            discount=float(payload.get("discount") or 0),
            note=payload.get("note"),
            queue_entry_id=payload.get("queue_entry_id"),
            actor=_actor(),
            organization_id=organization_id,
            collection_mode=payload.get("collection_mode"),
            pickup={
                "pickup_address": payload.get("pickup_address"),
                "pickup_city": payload.get("pickup_city") or payload.get("city"),
                "contact_phone": payload.get("contact_phone") or payload.get("phone"),
                "requested_date": payload.get("requested_date"),
                "requested_time_window": payload.get("requested_time_window")
                or payload.get("time_window"),
                "note": payload.get("collection_note") or payload.get("pickup_note"),
                "latitude": payload.get("latitude") or payload.get("pickup_latitude"),
                "longitude": payload.get("longitude") or payload.get("pickup_longitude"),
            },
        )
        db.session.commit()
        return {"success": True, "data": result}, 201
    except (ReceptionWorkspaceError, BusinessEngineError) as exc:
        db.session.rollback()
        return {"success": False, "error": str(exc)}, 400


@reception_workspace_bp.route("/orders/<order_ref>", methods=["GET"])
@reception_api_read
def orders_get(order_ref: str):
    """Milestone 2 — order detail with payment summary, payment, and invoice."""
    try:
        return {"success": True, "data": get_order_with_payment(order_ref)}, 200
    except BusinessEngineError as exc:
        return {"success": False, "error": str(exc)}, 404
    except ReceptionWorkspaceError as exc:
        return {"success": False, "error": str(exc)}, 404


@reception_workspace_bp.route("/orders/<order_ref>/payment", methods=["POST"])
@reception_api_write
def orders_payment(order_ref: str):
    payload = request.get_json(silent=True) or {}
    raw_amount = payload.get("amount")
    amount = float(raw_amount) if raw_amount is not None and raw_amount != "" else None
    idempotency_key = (
        payload.get("idempotency_key")
        or request.headers.get("Idempotency-Key")
        or request.headers.get("Idempotency-key")
    )
    try:
        result = collect_payment(
            order_ref,
            payment_method=payload.get("payment_method", "cash"),
            receipt_number=payload.get("receipt_number"),
            amount=amount,
            idempotency_key=idempotency_key,
            actor=_actor(),
        )
        db.session.commit()
        return {"success": True, "data": result}, 200
    except (ReceptionWorkspaceError, BusinessEngineError) as exc:
        db.session.rollback()
        return {"success": False, "error": str(exc)}, 400


@reception_workspace_bp.route("/orders/<order_ref>/payments", methods=["GET"])
@reception_api_read
def orders_payment_history(order_ref: str):
    """Payment Engine — payment history for an order."""
    try:
        return {"success": True, "data": get_payment_history(order_ref)}, 200
    except ReceptionWorkspaceError as exc:
        return {"success": False, "error": str(exc)}, 404
    except BusinessEngineError as exc:
        return {"success": False, "error": str(exc)}, 404


@reception_workspace_bp.route("/orders/<order_ref>/receipts", methods=["GET"])
@reception_api_read
def orders_receipts(order_ref: str):
    from app.reception_workspace.receipt_engine import list_receipts_for_order

    try:
        return {"success": True, "data": list_receipts_for_order(order_ref)}, 200
    except ReceptionWorkspaceError as exc:
        return {"success": False, "error": str(exc)}, 404


@reception_workspace_bp.route("/receipts/<receipt_ref>", methods=["GET"])
@reception_api_read
def receipt_get(receipt_ref: str):
    from app.reception_workspace.receipt_engine import get_receipt

    try:
        return {"success": True, "data": get_receipt(receipt_ref)}, 200
    except ReceptionWorkspaceError as exc:
        return {"success": False, "error": str(exc)}, 404


@reception_workspace_bp.route("/receipts/<receipt_ref>/preview", methods=["GET"])
@reception_api_read
def receipt_preview(receipt_ref: str):
    from app.reception_workspace.receipt_engine import preview_receipt

    fmt = (request.args.get("format") or "standard").strip().lower()
    try:
        return {"success": True, "data": preview_receipt(receipt_ref, format=fmt)}, 200
    except ReceptionWorkspaceError as exc:
        message = str(exc)
        status = 404 if "not found" in message.lower() else 400
        return {"success": False, "error": message}, status


@reception_workspace_bp.route("/receipts/<receipt_ref>/print", methods=["POST"])
@reception_api_write
def receipt_print(receipt_ref: str):
    from app.reception_workspace.receipt_engine import record_print

    payload = request.get_json(silent=True) or {}
    fmt = (payload.get("format") or "standard").strip().lower()
    try:
        result = record_print(receipt_ref, format=fmt, actor=_actor(), as_reprint=False)
        db.session.commit()
        return {"success": True, "data": result}, 200
    except ReceptionWorkspaceError as exc:
        db.session.rollback()
        message = str(exc)
        status = 404 if "not found" in message.lower() else 400
        return {"success": False, "error": message}, status


@reception_workspace_bp.route("/receipts/<receipt_ref>/reprint", methods=["POST"])
@reception_api_write
def receipt_reprint(receipt_ref: str):
    from app.reception_workspace.receipt_engine import reprint_receipt

    payload = request.get_json(silent=True) or {}
    fmt = (payload.get("format") or "standard").strip().lower()
    try:
        result = reprint_receipt(receipt_ref, format=fmt, actor=_actor())
        db.session.commit()
        return {"success": True, "data": result}, 200
    except ReceptionWorkspaceError as exc:
        db.session.rollback()
        message = str(exc)
        status = 404 if "not found" in message.lower() else 400
        return {"success": False, "error": message}, status


@reception_workspace_bp.route("/receipts/<receipt_ref>/pdf", methods=["GET"])
@reception_api_read
def receipt_pdf(receipt_ref: str):
    from flask import Response

    from app.reception_workspace.receipt_engine import generate_receipt_pdf

    try:
        result = generate_receipt_pdf(receipt_ref, actor=_actor(), persist=True)
        db.session.commit()
        return Response(
            result["pdf_bytes"],
            mimetype="application/pdf",
            headers={
                "Content-Disposition": f'inline; filename="{result["filename"]}"',
                "X-Receipt-Code": result["receipt"]["receipt_code"],
            },
        )
    except ReceptionWorkspaceError as exc:
        db.session.rollback()
        message = str(exc)
        status = 404 if "not found" in message.lower() else 400
        return {"success": False, "error": message}, status


@reception_workspace_bp.route("/receipts/<receipt_ref>/cancel", methods=["POST"])
@reception_api_write
def receipt_cancel(receipt_ref: str):
    from app.reception_workspace.receipt_engine import cancel_receipt

    payload = request.get_json(silent=True) or {}
    try:
        result = cancel_receipt(
            receipt_ref,
            reason=payload.get("reason"),
            actor=_actor(),
        )
        db.session.commit()
        return {"success": True, "data": result}, 200
    except ReceptionWorkspaceError as exc:
        db.session.rollback()
        message = str(exc)
        status = 404 if "not found" in message.lower() else 400
        return {"success": False, "error": message}, status


@reception_workspace_bp.route("/payments/<payment_ref>/receipt", methods=["POST"])
@reception_api_write
def payment_issue_receipt(payment_ref: str):
    from app.reception_workspace.receipt_engine import issue_receipt_for_payment

    payload = request.get_json(silent=True) or {}
    try:
        receipt = issue_receipt_for_payment(
            payment_ref,
            preferred_format=(payload.get("format") or "standard"),
            actor=_actor(),
        )
        db.session.commit()
        return {"success": True, "data": {"receipt": receipt.to_dict()}}, 201
    except ReceptionWorkspaceError as exc:
        db.session.rollback()
        message = str(exc)
        status = 404 if "not found" in message.lower() else 400
        return {"success": False, "error": message}, status


@reception_workspace_bp.route("/orders/<order_ref>/collection", methods=["POST"])
@reception_api_write
def orders_collection(order_ref: str):
    payload = request.get_json(silent=True) or {}
    try:
        result = create_collection_after_payment(
            order_ref,
            collector_name=payload.get("collector_name", "Walk-in Collector"),
            pickup_address=payload.get("pickup_address", "Reception Desk"),
            actor=_actor(),
        )
        db.session.commit()
        return {"success": True, "data": result}, 201
    except (ReceptionWorkspaceError, BusinessEngineError) as exc:
        db.session.rollback()
        return {"success": False, "error": str(exc)}, 400


@reception_workspace_bp.route("/orders/<order_ref>/barcode", methods=["GET"])
@reception_api_read
def orders_barcode(order_ref: str):
    """Generate or reprint stable barcodes (paid orders only)."""
    include_labels = (request.args.get("labels") or "").lower() in {"1", "true", "yes"}
    try:
        if include_labels:
            from app.reception_workspace.barcode_engine import get_barcode_bundle

            return {"success": True, "data": get_barcode_bundle(order_ref)}, 200
        return {"success": True, "data": generate_barcodes(order_ref)}, 200
    except ReceptionWorkspaceError as exc:
        message = str(exc)
        status = 404 if "not found" in message.lower() else 400
        return {"success": False, "error": message}, status


@reception_workspace_bp.route("/orders/<order_ref>/barcode/labels", methods=["GET"])
@reception_api_read
def orders_barcode_labels(order_ref: str):
    from app.reception_workspace.barcode_engine import build_labels

    types_raw = (request.args.get("types") or "").strip()
    types = [t for t in types_raw.split(",") if t.strip()] if types_raw else None
    try:
        return {"success": True, "data": build_labels(order_ref, types=types)}, 200
    except ReceptionWorkspaceError as exc:
        message = str(exc)
        status = 404 if "not found" in message.lower() else 400
        return {"success": False, "error": message}, status


@reception_workspace_bp.route("/orders/<order_ref>/barcode/preview", methods=["GET"])
@reception_api_read
def orders_barcode_preview(order_ref: str):
    from app.reception_workspace.barcode_engine import preview_labels

    fmt = (request.args.get("format") or "standard").strip().lower()
    types_raw = (request.args.get("types") or "").strip()
    types = [t for t in types_raw.split(",") if t.strip()] if types_raw else None
    try:
        return {
            "success": True,
            "data": preview_labels(order_ref, types=types, format=fmt),
        }, 200
    except ReceptionWorkspaceError as exc:
        message = str(exc)
        status = 404 if "not found" in message.lower() else 400
        return {"success": False, "error": message}, status


@reception_workspace_bp.route("/orders/<order_ref>/barcode/print", methods=["POST"])
@reception_api_write
def orders_barcode_print(order_ref: str):
    from app.reception_workspace.barcode_engine import print_labels

    payload = request.get_json(silent=True) or {}
    types = payload.get("types")
    if isinstance(types, str):
        types = [t for t in types.split(",") if t.strip()]
    try:
        result = print_labels(
            order_ref,
            types=types,
            format=(payload.get("format") or "standard"),
            printer=(payload.get("printer") or "browser"),
            actor=_actor(),
        )
        db.session.commit()
        return {"success": True, "data": result}, 200
    except ReceptionWorkspaceError as exc:
        db.session.rollback()
        message = str(exc)
        status = 404 if "not found" in message.lower() else 400
        return {"success": False, "error": message}, status


@reception_workspace_bp.route("/barcode/printers", methods=["GET"])
@reception_api_read
def barcode_printers():
    from app.reception_workspace.printers import list_printers

    return {"success": True, "data": {"printers": list_printers()}}, 200


@reception_workspace_bp.route("/qr/kinds", methods=["GET"])
@reception_api_read
def qr_kinds():
    from app.reception_workspace.qr_engine import list_qr_kinds

    return {"success": True, "data": {"kinds": list_qr_kinds()}}, 200


@reception_workspace_bp.route("/qr/verify", methods=["POST"])
@reception_api_read
def qr_verify():
    from app.reception_workspace.qr_engine import verify_qr_payload

    payload = request.get_json(silent=True) or {}
    try:
        result = verify_qr_payload(
            payload.get("payload") or "",
            order_ref=payload.get("order_ref") or payload.get("order_code"),
        )
        return {"success": True, "data": result}, 200
    except ReceptionWorkspaceError as exc:
        message = str(exc)
        status = 404 if "not found" in message.lower() else 400
        return {"success": False, "error": message}, status


@reception_workspace_bp.route("/orders/<order_ref>/qr", methods=["GET"])
@reception_api_read
def orders_qr_bundle(order_ref: str):
    from app.reception_workspace.qr_engine import build_qr_bundle, preview_qr_html

    kinds_raw = (request.args.get("kinds") or "").strip()
    kinds = [k for k in kinds_raw.split(",") if k.strip()] if kinds_raw else None
    amount_raw = request.args.get("amount")
    amount = float(amount_raw) if amount_raw not in (None, "") else None
    include_images = (request.args.get("images") or "1").lower() not in {"0", "false", "no"}
    include_html = (request.args.get("preview") or "").lower() in {"1", "true", "yes"}
    try:
        bundle = build_qr_bundle(
            order_ref,
            kinds=kinds,
            amount=amount,
            include_images=include_images,
        )
        if include_html:
            bundle["html"] = preview_qr_html(bundle)
        return {"success": True, "data": bundle}, 200
    except ReceptionWorkspaceError as exc:
        message = str(exc)
        status = 404 if "not found" in message.lower() else 400
        return {"success": False, "error": message}, status
    except ValueError as exc:
        return {"success": False, "error": str(exc)}, 400


@reception_workspace_bp.route("/orders/<order_ref>/qr/preview", methods=["GET"])
@reception_api_read
def orders_qr_preview(order_ref: str):
    from app.reception_workspace.qr_engine import build_qr_bundle, preview_qr_html

    kinds_raw = (request.args.get("kinds") or "").strip()
    kinds = [k for k in kinds_raw.split(",") if k.strip()] if kinds_raw else None
    amount_raw = request.args.get("amount")
    amount = float(amount_raw) if amount_raw not in (None, "") else None
    try:
        bundle = build_qr_bundle(order_ref, kinds=kinds, amount=amount, include_images=True)
        return {
            "success": True,
            "data": {
                **bundle,
                "html": preview_qr_html(bundle),
            },
        }, 200
    except ReceptionWorkspaceError as exc:
        message = str(exc)
        status = 404 if "not found" in message.lower() else 400
        return {"success": False, "error": message}, status
    except ValueError as exc:
        return {"success": False, "error": str(exc)}, 400


@reception_workspace_bp.route("/orders/<order_ref>/request-form", methods=["GET"])
@reception_api_read
def orders_request_form(order_ref: str):
    """Milestone 3 — laboratory requisition HTML (paid orders only)."""
    try:
        result = render_request_form(order_ref)
        return {"success": True, "data": result}, 200
    except ReceptionWorkspaceError as exc:
        message = str(exc)
        status = 404 if "not found" in message.lower() else 400
        return {"success": False, "error": message}, status


@reception_workspace_bp.route("/orders/<order_ref>/lab-handoff", methods=["POST"])
@reception_api_write
def orders_lab_handoff(order_ref: str):
    """Milestone 4 — hand paid+documented order into laboratory incoming queue."""
    payload = request.get_json(silent=True) or {}
    try:
        result = handoff_to_laboratory(
            order_ref,
            collector_name=payload.get("collector_name") or "Reception Desk",
            pickup_address=payload.get("pickup_address") or "Reception Desk",
            laboratory_name=payload.get("laboratory_name") or "Central Laboratory",
            laboratory_id=payload.get("laboratory_id"),
            actor=_actor(),
            desk_complete=payload.get("desk_complete", True) is not False,
        )
        db.session.commit()
        return {"success": True, "data": result}, 200
    except ReceptionWorkspaceError as exc:
        db.session.rollback()
        message = str(exc)
        if "not found" in message.lower():
            return {"success": False, "error": message}, 404
        return {"success": False, "error": message}, 400
    except BusinessEngineError as exc:
        db.session.rollback()
        return {"success": False, "error": str(exc)}, 400


@reception_workspace_bp.route("/orders/<order_ref>/lab-handoff", methods=["GET"])
@reception_api_read
def orders_lab_handoff_status(order_ref: str):
    """Milestone 4 — refresh handoff persistence (order/sample status + queue ref)."""
    try:
        return {"success": True, "data": get_lab_handoff_status(order_ref)}, 200
    except ReceptionWorkspaceError as exc:
        message = str(exc)
        status = 404 if "not found" in message.lower() else 400
        return {"success": False, "error": message}, status


@reception_workspace_bp.route("/lab-queue", methods=["GET"])
@reception_api_read
def lab_queue_dashboard_route():
    from app.reception_workspace.lab_queue_engine import lab_queue_dashboard

    stage = (request.args.get("stage") or "").strip() or None
    priority = (request.args.get("priority") or "").strip() or None
    since = (request.args.get("since") or "").strip() or None
    version_raw = request.args.get("version")
    version = int(version_raw) if version_raw not in (None, "") else None
    limit_raw = request.args.get("limit")
    limit = int(limit_raw) if limit_raw not in (None, "") else 100
    try:
        return {
            "success": True,
            "data": lab_queue_dashboard(
                stage=stage,
                priority=priority,
                since=since,
                version=version,
                limit=limit,
            ),
        }, 200
    except ReceptionWorkspaceError as exc:
        return {"success": False, "error": str(exc)}, 400
    except ValueError as exc:
        return {"success": False, "error": str(exc)}, 400


@reception_workspace_bp.route("/lab-queue/stats", methods=["GET"])
@reception_api_read
def lab_queue_stats_route():
    from app.reception_workspace.lab_queue_engine import lab_queue_statistics

    return {"success": True, "data": lab_queue_statistics()}, 200


@reception_workspace_bp.route("/lab-queue/refresh", methods=["GET"])
@reception_api_read
def lab_queue_refresh_route():
    from app.reception_workspace.lab_queue_engine import lab_queue_refresh

    since = (request.args.get("since") or "").strip() or None
    version_raw = request.args.get("version")
    version = int(version_raw) if version_raw not in (None, "") else None
    try:
        return {
            "success": True,
            "data": lab_queue_refresh(since=since, version=version),
        }, 200
    except ValueError as exc:
        return {"success": False, "error": str(exc)}, 400


@reception_workspace_bp.route("/lab-queue/orders/<order_ref>/enqueue", methods=["POST"])
@reception_api_write
def lab_queue_enqueue(order_ref: str):
    """Enqueue via handoff (paid → barcode → lab queue → waiting)."""
    payload = request.get_json(silent=True) or {}
    try:
        result = handoff_to_laboratory(
            order_ref,
            collector_name=payload.get("collector_name") or "Reception Desk",
            pickup_address=payload.get("pickup_address") or "Reception Desk",
            laboratory_name=payload.get("laboratory_name") or "Central Laboratory",
            laboratory_id=payload.get("laboratory_id"),
            actor=_actor(),
            desk_complete=payload.get("desk_complete", True) is not False,
        )
        if payload.get("priority"):
            from app.reception_workspace.lab_queue_engine import set_lab_queue_priority

            result["lab_queue"] = set_lab_queue_priority(
                order_ref, priority=payload["priority"], actor=_actor()
            )
        db.session.commit()
        return {"success": True, "data": result}, 200
    except ReceptionWorkspaceError as exc:
        db.session.rollback()
        message = str(exc)
        status = 404 if "not found" in message.lower() else 400
        return {"success": False, "error": message}, status
    except BusinessEngineError as exc:
        db.session.rollback()
        return {"success": False, "error": str(exc)}, 400


@reception_workspace_bp.route("/lab-queue/orders/<order_ref>/advance", methods=["POST"])
@reception_api_write
def lab_queue_advance(order_ref: str):
    from app.reception_workspace.lab_queue_engine import advance_lab_queue

    payload = request.get_json(silent=True) or {}
    try:
        result = advance_lab_queue(
            order_ref,
            to_stage=payload.get("to") or payload.get("stage") or "",
            actor=_actor(),
        )
        db.session.commit()
        return {"success": True, "data": result}, 200
    except ReceptionWorkspaceError as exc:
        db.session.rollback()
        message = str(exc)
        status = 404 if "not found" in message.lower() else 400
        return {"success": False, "error": message}, status


@reception_workspace_bp.route("/lab-queue/orders/<order_ref>/priority", methods=["POST"])
@reception_api_write
def lab_queue_priority(order_ref: str):
    from app.reception_workspace.lab_queue_engine import set_lab_queue_priority

    payload = request.get_json(silent=True) or {}
    try:
        result = set_lab_queue_priority(
            order_ref,
            priority=payload.get("priority") or "",
            actor=_actor(),
        )
        db.session.commit()
        return {"success": True, "data": result}, 200
    except ReceptionWorkspaceError as exc:
        db.session.rollback()
        message = str(exc)
        status = 404 if "not found" in message.lower() else 400
        return {"success": False, "error": message}, status


@reception_workspace_bp.route("/desk-collections", methods=["GET"])
@reception_api_read
def desk_collections_queue():
    """AT_RECEPTION worklist — never mixed into field Collector Queue."""
    from app.sample_collection_workspace.collection_routing import list_reception_desk_queue

    try:
        payload = list_reception_desk_queue(
            status=request.args.get("status"),
            location=request.args.get("location"),
            date_from=request.args.get("date") or request.args.get("date_from"),
            date_to=request.args.get("date_to"),
            role=session.get("role") or request.headers.get("X-User-Role"),
            organization_id=request.headers.get("X-Organization-ID")
            or request.headers.get("X-Organization-Id"),
        )
        return {"success": True, "data": payload}, 200
    except Exception as exc:
        return {"success": False, "error": str(exc)}, 400


@reception_workspace_bp.route("/field-collection-requests", methods=["GET"])
@reception_api_read
def field_collection_requests():
    """HOME/CLINIC requests visible to reception (read-only board)."""
    from app.sample_collection_workspace.collection_routing import list_field_collector_queue

    try:
        payload = list_field_collector_queue(
            status=request.args.get("status"),
            location=request.args.get("location"),
            date_from=request.args.get("date") or request.args.get("date_from"),
            date_to=request.args.get("date_to"),
            role=session.get("role") or request.headers.get("X-User-Role"),
            organization_id=request.headers.get("X-Organization-ID")
            or request.headers.get("X-Organization-Id"),
        )
        return {"success": True, "data": payload}, 200
    except Exception as exc:
        return {"success": False, "error": str(exc)}, 400


@reception_workspace_bp.route("/sample-queue", methods=["GET"])
@reception_api_read
def sample_queue_dashboard_route():
    from app.reception_workspace.sample_queue_engine import sample_queue_dashboard

    stage = (request.args.get("stage") or "").strip() or None
    version_raw = request.args.get("version")
    version = int(version_raw) if version_raw not in (None, "") else None
    limit_raw = request.args.get("limit")
    limit = int(limit_raw) if limit_raw not in (None, "") else 100
    try:
        return {
            "success": True,
            "data": sample_queue_dashboard(stage=stage, version=version, limit=limit),
        }, 200
    except ReceptionWorkspaceError as exc:
        return {"success": False, "error": str(exc)}, 400
    except ValueError as exc:
        return {"success": False, "error": str(exc)}, 400


@reception_workspace_bp.route("/sample-queue/stats", methods=["GET"])
@reception_api_read
def sample_queue_stats_route():
    from app.reception_workspace.sample_queue_engine import sample_queue_statistics

    return {"success": True, "data": sample_queue_statistics()}, 200


@reception_workspace_bp.route("/sample-queue/refresh", methods=["GET"])
@reception_api_read
def sample_queue_refresh_route():
    from app.reception_workspace.sample_queue_engine import sample_queue_refresh

    version_raw = request.args.get("version")
    version = int(version_raw) if version_raw not in (None, "") else None
    try:
        return {"success": True, "data": sample_queue_refresh(version=version)}, 200
    except ValueError as exc:
        return {"success": False, "error": str(exc)}, 400


@reception_workspace_bp.route("/sample-queue/orders/<order_ref>/enqueue", methods=["POST"])
@reception_api_write
def sample_queue_enqueue(order_ref: str):
    from app.reception_workspace.sample_queue_engine import ensure_sample_queue_item

    payload = request.get_json(silent=True) or {}
    try:
        result = ensure_sample_queue_item(
            order_ref,
            actor=_actor(),
            location=payload.get("location"),
            note=payload.get("note"),
            sync_collection=payload.get("sync_collection", True) is not False,
        )
        db.session.commit()
        return {"success": True, "data": result}, 200
    except ReceptionWorkspaceError as exc:
        db.session.rollback()
        message = str(exc)
        status = 404 if "not found" in message.lower() else 400
        return {"success": False, "error": message}, status


@reception_workspace_bp.route("/sample-queue/orders/<order_ref>/advance", methods=["POST"])
@reception_api_write
def sample_queue_advance(order_ref: str):
    from app.reception_workspace.sample_queue_engine import advance_sample_queue

    payload = request.get_json(silent=True) or {}
    try:
        result = advance_sample_queue(
            order_ref,
            to_stage=payload.get("to") or payload.get("stage") or "",
            actor=_actor(),
            note=payload.get("note"),
            location=payload.get("location"),
            sync_collection=payload.get("sync_collection", True) is not False,
        )
        db.session.commit()
        return {"success": True, "data": result}, 200
    except ReceptionWorkspaceError as exc:
        db.session.rollback()
        message = str(exc)
        status = 404 if "not found" in message.lower() else 400
        return {"success": False, "error": message}, status


@reception_workspace_bp.route("/sample-queue/orders/<order_ref>/track", methods=["GET"])
@reception_api_read
def sample_queue_track(order_ref: str):
    from app.reception_workspace.sample_queue_engine import track_sample

    try:
        return {"success": True, "data": track_sample(order_ref)}, 200
    except ReceptionWorkspaceError as exc:
        message = str(exc)
        status = 404 if "not found" in message.lower() else 400
        return {"success": False, "error": message}, status


@reception_workspace_bp.route("/sample-queue/orders/<order_ref>/history", methods=["GET"])
@reception_api_read
def sample_queue_history(order_ref: str):
    from app.reception_workspace.sample_queue_engine import get_sample_queue_history

    try:
        return {
            "success": True,
            "data": {"order_code": order_ref, "history": get_sample_queue_history(order_ref)},
        }, 200
    except ReceptionWorkspaceError as exc:
        return {"success": False, "error": str(exc)}, 400


@reception_workspace_bp.route("/sample-queue/orders/<order_ref>/tracking", methods=["POST"])
@reception_api_write
def sample_queue_tracking_update(order_ref: str):
    from app.reception_workspace.sample_queue_engine import update_sample_tracking

    payload = request.get_json(silent=True) or {}
    try:
        result = update_sample_tracking(
            order_ref,
            location=payload.get("location"),
            note=payload.get("note"),
            actor=_actor(),
        )
        db.session.commit()
        return {"success": True, "data": result}, 200
    except ReceptionWorkspaceError as exc:
        db.session.rollback()
        message = str(exc)
        status = 404 if "not found" in message.lower() else 400
        return {"success": False, "error": message}, status


@reception_workspace_bp.route("/queue", methods=["GET"])
@reception_api_read
def queue():
    dash = workspace_dashboard()
    return {"success": True, "data": dash.get("workflow_queue", []), "kpis": dash.get("kpis", {})}, 200


@reception_workspace_bp.route("/report", methods=["GET"])
@reception_api_read
def report():
    return {"success": True, "data": reception_workspace_report()}, 200


@reception_workspace_bp.route("/payment-report", methods=["GET"])
@reception_api_read
def payment_report_route():
    return {"success": True, "data": payment_report()}, 200


@reception_workspace_bp.route("/queue-report", methods=["GET"])
@reception_api_read
def queue_report_route():
    return {"success": True, "data": queue_report()}, 200
